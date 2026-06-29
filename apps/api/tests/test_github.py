"""Tests for the GitHub App integration (signature, app JWT, PR handling, webhook)."""

import hashlib
import hmac

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.integrations.github import (
    build_app_jwt,
    handle_pull_request_event,
    verify_webhook_signature,
)


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_signature_valid_and_invalid():
    secret = "topsecret"
    body = b'{"action":"opened"}'
    assert verify_webhook_signature(secret, body, _sign(secret, body))
    assert not verify_webhook_signature(secret, body, "sha256=deadbeef")
    assert not verify_webhook_signature(secret, body, None)
    assert not verify_webhook_signature("", body, _sign(secret, body))


def test_build_app_jwt_is_rs256_and_verifiable():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    token = build_app_jwt("12345", pem)
    decoded = jwt.decode(token, pub, algorithms=["RS256"])
    assert decoded["iss"] == "12345"
    assert decoded["exp"] > decoded["iat"]


class _FakeGitHubClient:
    def __init__(self):
        self.review = None
        self.check = None

    async def get_pull_request_files(self, repo, number):
        return [
            {"filename": "app/db.py", "status": "modified", "patch": "@@ -1 +1 @@\n+query = f'... {uid}'"},
            {"filename": "deleted.py", "status": "removed", "patch": None},
        ]

    async def create_review(self, repo, number, body, comments, event="COMMENT"):
        self.review = {"body": body, "comments": comments, "event": event}
        return {"id": 1}

    async def create_check_run(self, repo, head_sha, *, conclusion, title, summary):
        self.check = {"conclusion": conclusion, "summary": summary}
        return {"id": 2}

    async def close(self):
        pass


def _pr_payload(action="opened"):
    return {
        "action": action,
        "number": 7,
        "pull_request": {"number": 7, "head": {"sha": "abc123"}},
        "repository": {"full_name": "acme/widgets"},
        "installation": {"id": 999},
    }


@pytest.mark.asyncio
async def test_handle_pr_posts_blocking_review_on_critical_finding():
    fake = _FakeGitHubClient()

    async def fake_reviewer(filename, patch):
        return [{"severity": "critical", "title": "SQL injection", "detail": "f-string", "line": 1, "suggestion": "params"}]

    result = await handle_pull_request_event(
        _pr_payload(),
        client_factory=lambda iid: _ret(fake),
        reviewer=fake_reviewer,
    )
    assert result["findings"] == 1
    assert result["blocking"] == 1
    assert fake.review["event"] == "REQUEST_CHANGES"
    assert fake.review["comments"][0]["path"] == "app/db.py"
    assert fake.check["conclusion"] == "failure"


@pytest.mark.asyncio
async def test_handle_pr_passes_when_clean():
    fake = _FakeGitHubClient()

    async def clean_reviewer(filename, patch):
        return []

    result = await handle_pull_request_event(
        _pr_payload(),
        client_factory=lambda iid: _ret(fake),
        reviewer=clean_reviewer,
    )
    assert result["findings"] == 0
    assert fake.review["event"] == "COMMENT"
    assert fake.check["conclusion"] == "success"


@pytest.mark.asyncio
async def test_handle_pr_skips_irrelevant_action():
    result = await handle_pull_request_event(
        _pr_payload(action="closed"),
        client_factory=lambda iid: _ret(_FakeGitHubClient()),
        reviewer=None,
    )
    assert "skipped" in result


async def _ret(value):
    """Await-able that returns a pre-built fake client."""
    return value


# â”€â”€ Webhook route (needs app/DB via the standard client fixture) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_webhook_rejects_bad_signature(client, monkeypatch):
    from core.config import settings

    monkeypatch.setattr(settings, "github_webhook_secret", "whsec")
    resp = await client.post(
        "/api/v1/integrations/github/webhook",
        content=b'{"action":"opened"}',
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=bad"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_ping_with_valid_signature(client, monkeypatch):
    from core.config import settings

    secret = "whsec"
    monkeypatch.setattr(settings, "github_webhook_secret", secret)
    body = b'{"zen":"hi"}'
    resp = await client.post(
        "/api/v1/integrations/github/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": _sign(secret, body),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["pong"] is True
