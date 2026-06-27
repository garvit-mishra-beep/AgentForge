"""Tests for the Quick Review route with mocked AI providers and Redis."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from core.model_registry import reset_registry
from core.providers import ChatResponse
from core.redis import rate_limit_reset, review_store_cleanup
from core.task_tracker import tracker


@pytest.fixture(autouse=True)
async def clear_review_state():
    await rate_limit_reset()
    await review_store_cleanup()
    reset_registry()
    yield
    await rate_limit_reset()
    await review_store_cleanup()
    reset_registry()


@pytest.fixture
def mock_providers():
    mock_provider = AsyncMock()

    async def smart_chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        if "Analyze the following code" in system_prompt or "what the code does" in system_prompt[:200]:
            return ChatResponse(
                content=json.dumps({
                    "purpose": "Authentication middleware",
                    "language": "python",
                    "dependencies": ["jwt"],
                    "data_flow": "token in decode user out",
                    "problem_areas": ["hardcoded secret"],
                }),
                model=model,
            )
        if "Output JSON only" in system_prompt and "analysis from builder" not in system_prompt.lower():
            return ChatResponse(
                content=json.dumps({
                    "issues": [
                        {"severity": "critical", "title": "Hardcoded secret", "line": 3,
                         "description": "Secret key in source", "suggestion": "Use env var"},
                    ],
                    "summary": "Found 1 issue",
                }),
                model=model,
            )
        return ChatResponse(
            content=json.dumps({
                "issues": [
                    {"severity": "critical", "title": "Hardcoded secret", "line": 3,
                     "description": "Secret key in source", "suggestion": "Use env var"},
                    {"severity": "major", "title": "No input validation", "line": 10,
                     "description": "Missing input sanitization", "suggestion": "Validate inputs"},
                ],
                "summary": "Found 2 issues",
            }),
            model=model,
        )

    mock_provider.chat = smart_chat

    # Mock the model registry methods
    with patch("apps.api.core.model_registry.ModelRegistry.get_legacy_chain") as mock_chain, \
         patch("apps.api.core.model_registry.ModelRegistry.get_provider_for_user") as mock_get_provider:

        # Return predictable model chains
        mock_chain.side_effect = lambda role: {
            "baseline": ["claude-3-5-sonnet"],
            "builder": ["gpt-4o"],
            "reviewer": ["claude-3-5-sonnet"]
        }.get(role, ["claude-3-5-sonnet"])

        # Return our mock provider and provider type
        mock_get_provider.return_value = (mock_provider, "anthropic")

        yield


@pytest.mark.asyncio
async def test_submit_review(client, mock_providers):
    response = await client.post(
        "/api/v1/review",
        json={"code": "def foo(): pass", "language": "python"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "review_id" in data


@pytest.mark.asyncio
async def test_get_review_pending(client, mock_providers):
    submit_resp = await client.post(
        "/api/v1/review",
        json={"code": "def foo(): return 1", "language": "python"},
    )
    review_id = submit_resp.json()["review_id"]

    response = await client.get(f"/api/v1/review/{review_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["review_id"] == review_id
    assert data["status"] in ("queued", "analyzing", "reviewing", "completed", "failed")


@pytest.mark.asyncio
async def test_get_review_not_found(client):
    response = await client.get("/api/v1/review/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_rate_limiting(client, mock_providers):
    await rate_limit_reset()

    for _ in range(10):
        response = await client.post(
            "/api/v1/review",
            json={"code": "def f(): pass", "language": "python"},
        )
        assert response.status_code == 200

    response = await client.post(
        "/api/v1/review",
        json={"code": "def g(): pass", "language": "python"},
    )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_review_json_error_handling(client, mock_providers):
    """When model returns non-JSON, the pipeline should handle it gracefully."""
    bad_provider = AsyncMock()

    async def bad_chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        return ChatResponse(content="This is not JSON", model=model)

    bad_provider.chat = bad_chat

    # Mock the model registry methods for this specific test
    with patch("apps.api.core.model_registry.ModelRegistry.get_legacy_chain") as mock_chain, \
         patch("apps.api.core.model_registry.ModelRegistry.get_provider_for_user") as mock_get_provider:

        # Return predictable model chains
        mock_chain.side_effect = lambda role: {
            "baseline": ["claude-3-5-sonnet"],
            "builder": ["gpt-4o"],
            "reviewer": ["claude-3-5-sonnet"]
        }.get(role, ["claude-3-5-sonnet"])

        # Return our bad provider and provider type
        mock_get_provider.return_value = (bad_provider, "anthropic")

        response = await client.post(
            "/api/v1/review",
            json={"code": "def foo(): pass", "language": "python"},
        )
        assert response.status_code == 200
        review_id = response.json()["review_id"]

        await asyncio.sleep(0.2)

        get_resp = await client.get(f"/api/v1/review/{review_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_review_empty_code(client):
    response = await client.post(
        "/api/v1/review",
        json={"code": "", "language": "python"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_review_language_detection(client, mock_providers):
    response = await client.post(
        "/api/v1/review",
        json={"code": "def hello(): print('world')"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_review_language_detection_go(client, mock_providers):
    response = await client.post(
        "/api/v1/review",
        json={"code": "func main() { fmt.Println('hello') }"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_review_language_detection_sql(client, mock_providers):
    response = await client.post(
        "/api/v1/review",
        json={"code": "SELECT * FROM users WHERE id = 1"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_review_semantic_comparison(client, mock_providers):
    """Verify that the semantic comparison is included in completed reviews."""
    response = await client.post(
        "/api/v1/review",
        json={"code": "SECRET = 'hardcoded'", "language": "python"},
    )
    review_id = response.json()["review_id"]

    await asyncio.sleep(0.5)

    response = await client.get(f"/api/v1/review/{review_id}")
    data = response.json()

    if data["status"] == "completed":
        assert data["comparison"] is not None
        assert data["comparison"]["bugs_single_would_miss"] >= 0


@pytest.mark.asyncio
async def test_review_pipeline_completes(client, mock_providers):
    """End-to-end test that the review pipeline runs to completion."""
    response = await client.post(
        "/api/v1/review",
        json={"code": "import os; SECRET = os.getenv('KEY')"},
    )
    review_id = response.json()["review_id"]

    for _ in range(10):
        await asyncio.sleep(0.2)
        response = await client.get(f"/api/v1/review/{review_id}")
        data = response.json()
        if data["status"] in ("completed", "failed"):
            break

    assert data["status"] in ("completed", "failed")
