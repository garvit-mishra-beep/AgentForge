"""Tests for API key management endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_providers(client):
    response = await client.get("/api/v1/keys/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "openai" in data["providers"]
    assert "anthropic" in data["providers"]


@pytest.mark.asyncio
async def test_validate_key_format_only(client):
    response = await client.post(
        "/api/v1/keys/validate",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format_valid"] is True


@pytest.mark.asyncio
async def test_validate_key_invalid_format(client):
    response = await client.post(
        "/api/v1/keys/validate",
        json={"provider": "openai", "key": "invalid-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format_valid"] is False
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_create_api_key(client):
    response = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "openai"
    assert "id" in data
    assert data["is_enabled"] is True


@pytest.mark.asyncio
async def test_create_api_key_invalid_format(client):
    response = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "bad-key"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_duplicate_api_key(client):
    await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )

    response = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_api_keys(client):
    await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    await client.post(
        "/api/v1/keys",
        json={"provider": "anthropic", "key": "sk-ant-abcdefghijklmnopqrstuvwxyz"},
    )

    response = await client.get("/api/v1/keys")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_api_key(client):
    create_resp = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    key_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/keys/{key_id}")
    assert response.status_code == 200
    assert response.json()["provider"] == "openai"


@pytest.mark.asyncio
async def test_get_api_key_not_found(client):
    response = await client.get("/api/v1/keys/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_api_key(client):
    create_resp = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    key_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/keys/{key_id}",
        json={"is_enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False


@pytest.mark.asyncio
async def test_update_api_key_with_new_key(client):
    create_resp = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    key_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/keys/{key_id}",
        json={"key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
    )
    assert response.status_code == 200
    assert "****" in response.json()["key_preview"]


@pytest.mark.asyncio
async def test_delete_api_key(client):
    create_resp = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    key_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/keys/{key_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/keys/{key_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_api_key_not_found(client):
    response = await client.delete("/api/v1/keys/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_key_preview_masked(client):
    response = await client.post(
        "/api/v1/keys",
        json={"provider": "openai", "key": "sk-abcdefghijklmnopqrstuvwxyz"},
    )
    data = response.json()
    assert "****" in data["key_preview"]
    assert "abcdefghijklmnopqrstuvwxyz" not in data["key_preview"]



