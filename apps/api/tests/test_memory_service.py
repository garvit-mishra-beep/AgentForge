"""Tests for memory service edge cases."""

import uuid

import pytest

from app.main import app
from app.memory_service import (
    delete_memories_by_project,
    delete_memory,
    get_memories,
    get_memory,
    get_relevant_memories,
    store_memory,
    update_memory,
)

USER_1 = "00000000-0000-0000-0000-000000000001"
USER_2 = "00000000-0000-0000-0000-000000000002"
PROJ_1 = "00000000-0000-0000-0000-000000000010"
PROJ_2 = "00000000-0000-0000-0000-000000000011"


def _db():
    return app.state.db


@pytest.mark.asyncio
async def test_store_and_get_memory(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "test-key", "test content")
    assert mem_id is not None

    result = await get_memory(db, mem_id, USER_1)
    assert result is not None
    assert result["key"] == "test-key"
    assert result["content"] == "test content"


@pytest.mark.asyncio
async def test_get_memory_not_found(setup_db):
    db = _db()
    result = await get_memory(db, str(uuid.uuid4()), USER_1)
    assert result is None


@pytest.mark.asyncio
async def test_get_memory_wrong_user(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "key", "content")
    result = await get_memory(db, mem_id, USER_2)
    assert result is None


@pytest.mark.asyncio
async def test_get_memories_with_filters(setup_db):
    db = _db()
    # Insert user_2 so foreign key is satisfied; only used to verify scoping
    await db.execute("INSERT INTO users (id, email, name) VALUES ($1, 'user2@test.com', 'User 2') ON CONFLICT (id) DO NOTHING", USER_2)
    await store_memory(db, USER_1, "k1", "content a", tags=["tag1"])
    await store_memory(db, USER_1, "k2", "content b", memory_type="insight", importance=0.9, tags=["tag2"])
    await store_memory(db, USER_2, "k3", "other user", tags=["tag1"])

    all_user1 = await get_memories(db, USER_1)
    assert len(all_user1) == 2

    by_type = await get_memories(db, USER_1, memory_type="insight")
    assert len(by_type) == 1

    by_tag = await get_memories(db, USER_1, tags=["tag2"])
    assert len(by_tag) == 1

    by_search = await get_memories(db, USER_1, search="content")
    assert len(by_search) == 2

    by_importance = await get_memories(db, USER_1, min_importance=0.8)
    assert len(by_importance) == 1

    with_limit = await get_memories(db, USER_1, limit=1)
    assert len(with_limit) == 1

    with_offset = await get_memories(db, USER_1, limit=1, offset=1)
    assert len(with_offset) == 1


@pytest.mark.asyncio
async def test_get_relevant_memories(setup_db):
    db = _db()
    await store_memory(db, USER_1, "python-import", "How to import os module", tags=["python"])
    await store_memory(db, USER_1, "docker-deploy", "Docker deployment steps", tags=["docker"])

    results = await get_relevant_memories(db, USER_1, "python import")
    assert len(results) >= 1
    assert any("python" in r["key"] for r in results)

    no_match = await get_relevant_memories(db, USER_1, "xy")
    assert len(no_match) == 0


@pytest.mark.asyncio
async def test_update_memory(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "key", "old content")

    updated = await update_memory(db, mem_id, USER_1, content="new content", importance=0.9, tags=["updated"])
    assert updated is True

    result = await get_memory(db, mem_id, USER_1)
    assert result["content"] == "new content"
    assert result["importance"] == pytest.approx(0.9, rel=1e-3)
    assert "updated" in result["tags"]


@pytest.mark.asyncio
async def test_update_nonexistent_memory(setup_db):
    db = _db()
    result = await update_memory(db, str(uuid.uuid4()), USER_1, content="whatever")
    assert result is False


@pytest.mark.asyncio
async def test_update_no_fields(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "key", "content")
    result = await update_memory(db, mem_id, USER_1)
    assert result is True


@pytest.mark.asyncio
async def test_delete_memory(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "key", "content")
    assert await delete_memory(db, mem_id, USER_1) is True
    assert await get_memory(db, mem_id, USER_1) is None


@pytest.mark.asyncio
async def test_delete_memory_not_found(setup_db):
    db = _db()
    assert await delete_memory(db, str(uuid.uuid4()), USER_1) is False


@pytest.mark.asyncio
async def test_delete_memory_wrong_user(setup_db):
    db = _db()
    mem_id = await store_memory(db, USER_1, "key", "content")
    assert await delete_memory(db, mem_id, USER_2) is False


@pytest.mark.asyncio
async def test_delete_memories_by_project(setup_db):
    db = _db()
    await db.execute("INSERT INTO projects (id, name, created_by) VALUES ($1, 'Project 1', $2) ON CONFLICT (id) DO NOTHING", PROJ_1, USER_1)
    await db.execute("INSERT INTO projects (id, name, created_by) VALUES ($1, 'Project 2', $2) ON CONFLICT (id) DO NOTHING", PROJ_2, USER_1)
    await store_memory(db, USER_1, "k1", "c1", project_id=PROJ_1)
    await store_memory(db, USER_1, "k2", "c2", project_id=PROJ_1)
    await store_memory(db, USER_1, "k3", "c3", project_id=PROJ_2)

    deleted = await delete_memories_by_project(db, PROJ_1, USER_1)
    assert deleted == 2

    remaining = await get_memories(db, USER_1)
    assert len(remaining) == 1
