"""Tests for teams CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_team(client):
    response = await client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "A test team"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Team"
    assert data["description"] == "A test team"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_team_minimal(client):
    response = await client.post(
        "/api/v1/teams",
        json={"name": "Minimal Team"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Team"
    assert data["description"] is None


@pytest.mark.asyncio
async def test_list_teams(client):
    await client.post("/api/v1/teams", json={"name": "Team 1"})
    await client.post("/api/v1/teams", json={"name": "Team 2"})

    response = await client.get("/api/v1/teams")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_team(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "My Team"})
    team_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/teams/{team_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Team"


@pytest.mark.asyncio
async def test_get_team_not_found(client):
    response = await client.get("/api/v1/teams/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_team(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Old Name"})
    team_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/teams/{team_id}",
        json={"name": "New Name", "description": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated"


@pytest.mark.asyncio
async def test_delete_team(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "To Delete"})
    team_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/teams/{team_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/teams/{team_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_team_not_found(client):
    response = await client.delete("/api/v1/teams/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_team_member(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Team"})
    team_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "builder", "model": "qwen2.5-coder:7b"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "builder"
    assert data["model"] == "qwen2.5-coder:7b"


@pytest.mark.asyncio
async def test_add_duplicate_role(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Team"})
    team_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "builder", "model": "qwen2.5-coder:7b"},
    )

    response = await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "builder", "model": "qwen2.5-coder:3b"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_teams_with_members(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "Full Team"})
    team_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "team_lead", "model": "gpt-4"},
    )
    await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"role": "builder", "model": "claude-3"},
    )

    response = await client.get("/api/v1/teams")
    assert response.status_code == 200
    data = response.json()
    assert len(data[0]["members"]) == 2


@pytest.mark.asyncio
async def test_create_team_with_all_roles(client):
    create_resp = await client.post("/api/v1/teams", json={"name": "AI Team"})
    team_id = create_resp.json()["id"]

    for role in ["team_lead", "builder", "reviewer"]:
        await client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"role": role, "model": "qwen2.5-coder:7b"},
        )

    response = await client.get(f"/api/v1/teams/{team_id}")
    assert response.status_code == 200
    assert len(response.json()["members"]) == 3


@pytest.mark.asyncio
async def test_team_not_found_for_member_operations(client):
    response = await client.post(
        "/api/v1/teams/00000000-0000-0000-0000-000000000000/members",
        json={"role": "builder", "model": "test"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_team_pagination(client):
    for i in range(5):
        await client.post("/api/v1/teams", json={"name": f"Team {i}"})

    response = await client.get("/api/v1/teams?limit=2&offset=0")
    data = response.json()
    assert len(data) == 2
