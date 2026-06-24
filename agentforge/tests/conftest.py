from __future__ import annotations

import sys
import uuid
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock

sys.path.insert(0, "C:\\Users\\garvi\\AgentOS\\agentforge")

from apps.api.main import app
from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.core.security import hash_password
from apps.api.models import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def mock_db():
    """Return a mock async session with a configurable execute handler."""
    mock = AsyncMock()
    mock.flush = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    mock.refresh = AsyncMock()

    class MockResult:
        """Return None for scalar_one_or_none by default."""

        def scalar_one_or_none(self):
            return None

    def default_execute(stmt):
        return MockResult()

    mock.execute = AsyncMock(side_effect=default_execute)
    return mock


@pytest.fixture
async def anon_client():
    """Client without any dependency overrides (unauthenticated)."""
    app.dependency_overrides.clear()
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client(mock_db):
    """Override core dependencies for testing."""
    async def override_get_db():
        yield mock_db

    async def override_current_user():
        return {
            "sub": "testuser",
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "type": "jwt",
        }

    def override_tenant_id():
        return uuid.UUID("00000000-0000-0000-0000-000000000000")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_current_user
    app.dependency_overrides[get_tenant_id] = override_tenant_id

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client):
    login = await client.post(
        "/api/v1/auth/token",
        json={"username": "testuser", "password": "testpass"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
