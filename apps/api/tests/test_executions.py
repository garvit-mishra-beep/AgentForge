"""Tests for execution endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_executions_empty(client):
    response = await client.get("/api/v1/executions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_execution_not_found(client):
    response = await client.get("/api/v1/executions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_execution_detail_not_found(client):
    response = await client.get("/api/v1/executions/detail/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execution_with_team_and_task(client):
    team_resp = await client.post("/api/v1/teams", json={"name": "Exec Team"})
    team_id = team_resp.json()["id"]

    for role in ["team_lead", "builder", "reviewer"]:
        await client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"role": role, "model": "gpt-4o-mini"},
        )

    task_resp = await client.post(
        "/api/v1/tasks",
        json={"team_id": team_id, "title": "Exec Task", "description": "Test"},
    )
    task_id = task_resp.json()["id"]

    response = await client.get(f"/api/v1/executions/{task_id}")
    assert response.status_code == 404  # Execution created async, may not be ready


@pytest.mark.asyncio
async def test_execution_pagination(client):
    response = await client.get("/api/v1/executions?limit=10&offset=0")
    assert response.status_code == 200
