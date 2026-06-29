"""Tests for task creation and lifecycle."""

import pytest


@pytest.fixture
async def team_with_roles(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Task Team"})
    team_id = create_resp.json()["id"]

    for role in ["team_lead", "builder", "reviewer"]:
        await client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"role": role, "model": "qwen2.5-coder:7b"},
        )
    return team_id


@pytest.mark.asyncio
async def test_create_task(client, team_with_roles):
    response = await client.post(
        "/api/v1/tasks",
        json={
            "team_id": team_with_roles,
            "title": "Test Task",
            "description": "Build something",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_task_missing_roles(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Incomplete Team"})
    team_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "team_lead", "model": "gpt-4"},
    )

    response = await client.post(
        "/api/v1/tasks",
        json={
            "team_id": team_id,
            "title": "Task",
            "description": "Test",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "missing" in data["detail"].lower()


@pytest.mark.asyncio
async def test_list_tasks(client, team_with_roles):
    await client.post(
        "/api/v1/tasks",
        json={"team_id": team_with_roles, "title": "Task 1", "description": "First"},
    )
    await client.post(
        "/api/v1/tasks",
        json={"team_id": team_with_roles, "title": "Task 2", "description": "Second"},
    )

    response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_task(client, team_with_roles):
    create_resp = await client.post(
        "/api/v1/tasks",
        json={"team_id": team_with_roles, "title": "My Task", "description": "Details"},
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "My Task"


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    response = await client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_task_against_unowned_team_is_rejected(client):
    """A user cannot target a team they do not own (IDOR #4)."""
    import uuid as _uuid

    from httpx import ASGITransport, AsyncClient

    from app.auth import create_token
    from app.main import app

    # Attacker owns a valid, fully-staffed team of their own...
    db = app.state.db
    attacker_id = str(_uuid.uuid4())
    await db.execute(
        "INSERT INTO users (id, email, name, password_hash) VALUES ($1, $2, $3, $4)",
        attacker_id, f"atk-{attacker_id[:8]}@e.com", "Atk", "x",
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": f"Bearer {create_token(attacker_id)}"},
    ) as attacker:
        team = await attacker.post("/api/v1/teams", json={"name": "Atk Team"})
        attacker_team = team.json()["id"]
        for role in ["team_lead", "builder", "reviewer"]:
            await attacker.post(
                f"/api/v1/teams/{attacker_team}/members",
                json={"role": role, "model": "qwen2.5-coder:7b"},
            )

        # ...but tries to create a task against the *demo* user's team.
        victim_team = await client.post("/api/v1/teams", json={"name": "Victim Team"})
        victim_team_id = victim_team.json()["id"]
        for role in ["team_lead", "builder", "reviewer"]:
            await client.post(
                f"/api/v1/teams/{victim_team_id}/members",
                json={"role": role, "model": "qwen2.5-coder:7b"},
            )

        resp = await attacker.post(
            "/api/v1/tasks",
            json={"team_id": victim_team_id, "title": "x", "description": "y"},
        )
        assert resp.status_code == 404

    await db.execute("DELETE FROM teams WHERE created_by = $1", attacker_id)
    await db.execute("DELETE FROM users WHERE id = $1", attacker_id)


@pytest.mark.asyncio
async def test_get_task_messages(client, team_with_roles):
    create_resp = await client.post(
        "/api/v1/tasks",
        json={"team_id": team_with_roles, "title": "Task", "description": "Desc"},
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/tasks/{task_id}/messages")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_task_pagination(client, team_with_roles):
    for i in range(3):
        await client.post(
            "/api/v1/tasks",
            json={"team_id": team_with_roles, "title": f"Task {i}", "description": f"Desc {i}"},
        )

    response = await client.get("/api/v1/tasks?limit=2&offset=0")
    data = response.json()
    assert len(data) == 2
