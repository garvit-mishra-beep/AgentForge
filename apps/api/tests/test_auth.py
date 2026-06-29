"""Tests for authentication middleware and auth routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import DEMO_USER_ID, create_token, verify_token
from app.main import app
from core.config import settings
from core.redis import brute_force_reset


@pytest.mark.asyncio
async def test_auth_disabled_returns_demo_user(client):
    """When auth is disabled, all routes should still work."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_token_create_and_verify():
    token = create_token(DEMO_USER_ID)
    assert token is not None
    assert "." in token  # JWT format: header.payload.signature

    user_id = verify_token(token)
    assert user_id == DEMO_USER_ID


@pytest.mark.asyncio
async def test_expired_token_returns_none():
    settings.jwt_expire_minutes = -1
    token = create_token(DEMO_USER_ID)
    user_id = verify_token(token)
    assert user_id is None
    settings.jwt_expire_minutes = 480


@pytest.mark.asyncio
async def test_tampered_token_returns_none():
    token = create_token(DEMO_USER_ID)
    tampered = token[:-5] + "XXXXX"
    user_id = verify_token(tampered)
    assert user_id is None


@pytest.mark.asyncio
async def test_invalid_token_format():
    assert verify_token("") is None
    assert verify_token("invalid") is None
    assert verify_token("not.a.jwt") is None
    assert verify_token("eyJ.eyJ.Invalid") is None


@pytest.mark.asyncio
async def test_health_open_without_auth(client):
    """Health endpoint must be open even with auth enabled."""
    old = settings.auth_enabled
    settings.auth_enabled = True
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    settings.auth_enabled = old


@pytest.mark.asyncio
async def test_protected_route_requires_auth(setup_db):
    """When auth is enabled, protected routes return 401 without a token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/teams",
            json={"name": "test", "description": "test"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_brute_force_locks_login_after_attempts(setup_db):
    """After 5 failed logins, the endpoint returns 429."""
    await brute_force_reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for _ in range(5):
            resp = await ac.post("/api/v1/auth/login", json={
                "email": "nonexistent@test.com",
                "password": "wrongpass123",
            })
            assert resp.status_code == 401

        resp = await ac.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpass123",
        })
        assert resp.status_code == 429
        assert "Too many login attempts" in resp.json()["detail"]
    await brute_force_reset()


@pytest.mark.asyncio
async def test_refresh_token_with_invalid_token(client):
    """Refresh endpoint returns 401 for invalid refresh token."""
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid-token"})
    assert resp.status_code == 401


async def _register(ac, email="rot@test.com"):
    resp = await ac.post("/api/v1/auth/register", json={
        "email": email, "password": "testpass123", "name": "Rot",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_refresh_rotation_revokes_old_token(setup_db):
    """A refresh token is single-use: after rotation the old one is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        data = await _register(ac, "rotate@test.com")
        old_refresh = data["refresh_token"]

        first = await ac.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert first.status_code == 200
        new_refresh = first.json()["refresh_token"]
        assert new_refresh != old_refresh

        # Replaying the old (now rotated) token must fail.
        replay = await ac.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert replay.status_code == 401

        # The freshly issued token still works.
        ok = await ac.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
        assert ok.status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(setup_db):
    """After /logout the refresh token can no longer be used."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        data = await _register(ac, "logout@test.com")
        refresh_token = data["refresh_token"]
        headers = {"Authorization": f"Bearer {data['token']}"}

        out = await ac.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}, headers=headers,
        )
        assert out.status_code == 204

        resp = await ac.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(setup_db):
    """Registering the same email twice returns 409."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp1 = await ac.post("/api/v1/auth/register", json={
            "email": "dup@test.com",
            "password": "testpass123",
            "name": "Dup",
        })
        assert resp1.status_code == 201, f"First register: {resp1.text}"
        resp2 = await ac.post("/api/v1/auth/register", json={
            "email": "dup@test.com",
            "password": "testpass456",
            "name": "Dup2",
        })
        assert resp2.status_code == 409
        assert "already registered" in resp2.json()["detail"]
