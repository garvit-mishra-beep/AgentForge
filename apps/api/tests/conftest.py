import sys
sys.modules["langchain"] = None

from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import create_token
from app.main import app
from core.config import settings
from core.database import DatabasePool
from core.redis import rate_limit_reset, brute_force_reset

settings.auth_enabled = True

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


@asynccontextmanager
async def dummy_lifespan(app):
    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    app.router.lifespan_context = dummy_lifespan
    pool = DatabasePool()
    await pool.initialize()
    await pool.run_migrations()
    app.state.db = pool
    yield
    await pool.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_db):
    yield
    pool = app.state.db
    tables = [
        "agent_memories", "project_files", "project_teams", "projects",
        "task_messages", "executions", "tasks",
        "team_members", "teams", "api_keys",
    ]
    for table in tables:
        await pool.execute(f"DELETE FROM {table}")


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limits():
    await rate_limit_reset()
    await brute_force_reset()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    token = create_token(DEMO_USER_ID)
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
