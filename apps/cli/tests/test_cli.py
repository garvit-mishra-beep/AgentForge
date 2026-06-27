"""CLI tests using httpx MockTransport (no live server)."""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentforge_cli.client import AgentForgeClient  # noqa: E402
from agentforge_cli.__main__ import main  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTFORGE_CLI_CONFIG", str(tmp_path / "config.json"))


def make_client(handler, config=None):
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return AgentForgeClient(api_url="http://test/api/v1", config=config or {}, http=http)


def test_login_stores_tokens(tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    monkeypatch.setenv("AGENTFORGE_CLI_CONFIG", str(cfg))

    def handler(request):
        assert request.url.path == "/api/v1/auth/login"
        return httpx.Response(200, json={
            "token": "acc", "refresh_token": "ref", "user_id": "u",
            "email": "a@b.com", "name": "A",
        })

    client = make_client(handler)
    client.login("a@b.com", "pw")
    stored = json.loads(cfg.read_text())
    assert stored["token"] == "acc"
    assert stored["refresh_token"] == "ref"


def test_auto_refresh_on_401():
    calls = {"n": 0}

    def handler(request):
        path = request.url.path
        if path == "/api/v1/auth/refresh":
            return httpx.Response(200, json={"token": "newacc", "refresh_token": "newref"})
        # First protected call: token is stale -> 401. After refresh: success.
        auth = request.headers.get("Authorization")
        if auth == "Bearer stale":
            return httpx.Response(401, json={"detail": "expired"})
        assert auth == "Bearer newacc"
        calls["n"] += 1
        return httpx.Response(200, json={"id": "t1", "status": "pending", "title": "x"})

    client = make_client(handler, config={"token": "stale", "refresh_token": "ref"})
    task = client.get_task("t1")
    assert task["id"] == "t1"
    assert calls["n"] == 1


def test_review_and_wait_polls_until_complete():
    state = {"polls": 0}

    def handler(request):
        if request.method == "POST" and request.url.path == "/api/v1/review":
            return httpx.Response(200, json={"review_id": "r1", "status": "queued"})
        if request.url.path == "/api/v1/review/r1":
            state["polls"] += 1
            if state["polls"] < 2:
                return httpx.Response(200, json={"review_id": "r1", "status": "queued", "issues": []})
            return httpx.Response(200, json={
                "review_id": "r1", "status": "completed",
                "issues": [{"severity": "high", "title": "SQLi", "description": "bad", "suggestion": "use params"}],
                "summary": "1 issue",
            })
        return httpx.Response(404)

    client = make_client(handler, config={"token": "acc"})
    result = client.review_and_wait("code", poll_interval=0, sleep=lambda s: None)
    assert result["status"] == "completed"
    assert result["issues"][0]["title"] == "SQLi"
    assert state["polls"] == 2


def test_main_review_returns_nonzero_on_blocking(tmp_path, capsys):
    f = tmp_path / "x.py"
    f.write_text("def q(uid): return f'select {uid}'")

    def handler(request):
        if request.method == "POST" and request.url.path == "/api/v1/review":
            return httpx.Response(200, json={"review_id": "r1", "status": "queued"})
        return httpx.Response(200, json={
            "review_id": "r1", "status": "completed",
            "issues": [{"severity": "critical", "title": "SQL injection", "description": "d", "suggestion": "s"}],
        })

    def factory(api):
        return make_client(handler, config={"token": "acc"})

    rc = main(["review", str(f)], client_factory=factory)
    out = capsys.readouterr().out
    assert rc == 1
    assert "SQL injection" in out
    assert "blocking" in out


def test_main_review_clean_returns_zero(tmp_path, capsys):
    f = tmp_path / "x.py"
    f.write_text("def add(a, b):\n    return a + b\n")

    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"review_id": "r1", "status": "queued"})
        return httpx.Response(200, json={"review_id": "r1", "status": "completed", "issues": []})

    rc = main(["review", str(f)], client_factory=lambda api: make_client(handler, config={"token": "acc"}))
    out = capsys.readouterr().out
    assert rc == 0
    assert "No issues" in out
