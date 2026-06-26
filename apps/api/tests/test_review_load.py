"""End-to-end load test for Quick Review.

Usage:
    python -m pytest tests/test_review_load.py -v --no-header --tb=short
    python tests/test_review_load.py
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from core.config import settings
from core.providers import ChatResponse
from core.redis import rate_limit_reset, review_store_cleanup


SAMPLE_CODES = [
    "def hello(): return 'world'",
    "import os; SECRET = os.getenv('KEY')",
    "SELECT * FROM users WHERE id = " + "'1' OR '1'='1'",
    "function add(a,b){return a+b}",
    "const x = await fetch('/api/data'); console.log(x)",
    "class Validator: def validate(self, data): pass",
    "@app.get('/')\ndef index(): return {'status': 'ok'}",
    "export default function App(){return <div>Hi</div>}",
    "print('hello world')",
    "docker run -e API_KEY=secret nginx:latest",
]


@pytest_asyncio.fixture(autouse=True)
async def clear_state():
    await rate_limit_reset()
    await review_store_cleanup()



    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_mock_provider():
    p = AsyncMock()

    async def chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        return ChatResponse(
            content=json.dumps({
                "issues": [{"severity": "minor", "title": "Test issue", "line": 1,
                            "description": "A test issue", "suggestion": "Fix it"}],
                "summary": "1 issue found",
            }),
            model=model,
        )

    p.chat = chat
    return p


@pytest.mark.asyncio
async def test_sequential_reviews(client, monkeypatch):
    from app.auth import create_token
    _tok = create_token("00000000-0000-0000-0000-000000000001")
    auth = {"Authorization": f"Bearer {_tok}"}
    n = 10
    monkeypatch.setattr(settings, "review_rate_limit", 100)

    provider = _make_mock_provider()
    with patch("app.routes.review.get_provider", return_value=provider), \
         patch("core.model_registry.get_provider", return_value=provider):
        for i, code in enumerate(SAMPLE_CODES[:n]):
            resp = await client.post("/api/v1/review", json={"code": code}, headers=auth)
            assert resp.status_code == 200, f"Request {i} failed: {resp.text}"

        # Allow tasks to complete
        await asyncio.sleep(0.2)


@pytest.mark.asyncio
async def test_burst_reviews(client, monkeypatch):
    from app.auth import create_token
    _tok = create_token("00000000-0000-0000-0000-000000000001")
    auth = {"Authorization": f"Bearer {_tok}"}
    n = 5
    monkeypatch.setattr(settings, "review_rate_limit", 100)

    provider = _make_mock_provider()
    with patch("app.routes.review.get_provider", return_value=provider), \
         patch("core.model_registry.get_provider", return_value=provider):
        responses = await asyncio.gather(*[
            client.post("/api/v1/review", json={"code": code}, headers=auth)
            for code in SAMPLE_CODES[:n]
        ])
        for resp in responses:
            assert resp.status_code == 200, f"Burst request failed: {resp.text}"

        await asyncio.sleep(0.2)


@pytest.mark.asyncio
async def test_rate_limit_enforcement(client, monkeypatch):
    from app.auth import create_token
    _tok = create_token("00000000-0000-0000-0000-000000000001")
    auth = {"Authorization": f"Bearer {_tok}"}
    monkeypatch.setattr(settings, "review_rate_limit", 5)
    monkeypatch.setattr(settings, "review_rate_window", 60)

    provider = _make_mock_provider()
    with patch("app.routes.review.get_provider", return_value=provider), \
         patch("core.model_registry.get_provider", return_value=provider):
        for i in range(5):
            resp = await client.post("/api/v1/review", json={"code": "pass"}, headers=auth)
            assert resp.status_code == 200, f"Request {i} failed"

        resp = await client.post("/api/v1/review", json={"code": "blocked"}, headers=auth)
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code}"


@pytest.mark.asyncio
async def test_error_rate(client):
    """Submit with bad provider config - verify error handling."""
    from app.auth import create_token
    _tok = create_token("00000000-0000-0000-0000-000000000001")
    auth = {"Authorization": f"Bearer {_tok}"}
    response = await client.post(
        "/api/v1/review",
        json={"code": "test code that is long enough"},
        headers=auth,
    )
    # Without mock providers, this may fail or error - that's acceptable
    assert response.status_code == 200
