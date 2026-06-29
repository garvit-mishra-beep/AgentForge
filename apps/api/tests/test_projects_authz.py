"""Cross-tenant authorization tests for project file routes (IDOR regression).

These guard the fix for TOP_FINDINGS #1/#2: file metadata/download/delete routes
previously filtered by ``project_id`` only, letting any authenticated user reach
another tenant's files.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import create_token
from app.main import app

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
async def attacker_client(setup_db):
    """A second authenticated user that owns nothing in the demo tenant."""
    db = app.state.db
    attacker_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO users (id, email, name, password_hash) VALUES ($1, $2, $3, $4)",
        attacker_id, f"attacker-{attacker_id[:8]}@example.com", "Attacker", "x",
    )
    token = create_token(attacker_id)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    await db.execute("DELETE FROM users WHERE id = $1", attacker_id)


async def _create_project_with_file(client) -> tuple[str, str]:
    """Owner (demo user) creates a project and uploads one file."""
    proj = await client.post("/api/v1/projects", json={"name": "Victim Project"})
    project_id = proj.json()["id"]
    upload = await client.post(
        f"/api/v1/projects/{project_id}/upload",
        files={"file": ("secret.py", b"API_KEY = 'super-secret'\n", "text/x-python")},
    )
    assert upload.status_code == 201, upload.text
    file_id = upload.json()["id"]
    return project_id, file_id


@pytest.mark.asyncio
async def test_attacker_cannot_get_file_metadata(client, attacker_client):
    project_id, file_id = await _create_project_with_file(client)
    resp = await attacker_client.get(f"/api/v1/projects/{project_id}/files/{file_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_attacker_cannot_download_file(client, attacker_client):
    project_id, file_id = await _create_project_with_file(client)
    resp = await attacker_client.get(
        f"/api/v1/projects/{project_id}/files/{file_id}/download"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_attacker_cannot_delete_file(client, attacker_client):
    project_id, file_id = await _create_project_with_file(client)
    resp = await attacker_client.delete(f"/api/v1/projects/{project_id}/files/{file_id}")
    assert resp.status_code == 404
    # File still reachable by the legitimate owner.
    owner_view = await client.get(f"/api/v1/projects/{project_id}/files/{file_id}")
    assert owner_view.status_code == 200


@pytest.mark.asyncio
async def test_owner_can_access_own_file(client):
    project_id, file_id = await _create_project_with_file(client)
    resp = await client.get(f"/api/v1/projects/{project_id}/files/{file_id}")
    assert resp.status_code == 200
    assert resp.json()["filename"] == "secret.py"
