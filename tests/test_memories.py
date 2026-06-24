import pytest
from httpx import AsyncClient, ASGITransport
import pytest_asyncio

from apps.api.main import app
from apps.api.dependencies.auth import get_current_active_user

# Bypass authentication for testing endpoints
@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_active_user] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_memory_crud_and_search():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        project_key = "test-project-key-999"
        
        # 1. Clean up any leftover from previous runs (safety delete)
        await ac.delete(f"/api/workflows/memories/{project_key}")
        
        # 2. Test create memory
        create_payload = {
            "project_key": project_key,
            "description": "High performance microservice for caching auth tokens using redis",
            "architecture": {
                "objective": "Build redis cache",
                "phases": [
                    {"name": "Init", "description": "Setup docker-compose", "estimated_hours": 2}
                ]
            },
            "code_artifacts": [
                {
                    "name": "docker-compose.yml",
                    "type": "source_file",
                    "content": "version: '3.8'\nservices:\n  redis:\n    image: redis"
                }
            ]
        }
        
        response = await ac.post("/api/workflows/memories", json=create_payload)
        assert response.status_code == 201, f"Failed to create memory: {response.text}"
        data = response.json()
        assert data["project_key"] == project_key
        assert data["description"] == create_payload["description"]
        assert "id" in data
        
        memory_id = data["id"]
        
        # 3. Test list memories
        response = await ac.get("/api/workflows/memories")
        assert response.status_code == 200
        memories_list = response.json()
        assert len(memories_list) >= 1
        # Check if our project is in the list
        found = any(m["project_key"] == project_key for m in memories_list)
        assert found
        
        # 4. Test get memory by key
        response = await ac.get(f"/api/workflows/memories/{project_key}")
        assert response.status_code == 200
        assert response.json()["id"] == memory_id
        
        # 5. Test get memory by ID
        response = await ac.get(f"/api/workflows/memories/{memory_id}")
        assert response.status_code == 200
        assert response.json()["project_key"] == project_key

        # 6. Test search memories
        # Searching "caching auth tokens redis" should match our memory description
        response = await ac.get("/api/workflows/memories/search?q=caching+auth+tokens+redis")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) >= 1
        assert search_results[0]["project_key"] == project_key

        # 7. Test update memory
        update_payload = {
            "description": "Updated description for caching auth tokens",
            "architecture": {
                "objective": "Build redis cache updated",
            }
        }
        response = await ac.put(f"/api/workflows/memories/{project_key}", json=update_payload)
        assert response.status_code == 200
        updated_data = response.json()
        assert updated_data["description"] == update_payload["description"]
        assert updated_data["architecture"]["objective"] == "Build redis cache updated"
        
        # 8. Test delete memory
        response = await ac.delete(f"/api/workflows/memories/{project_key}")
        assert response.status_code == 200
        assert response.json()["message"] == "Project memory deleted successfully"

        # 9. Verify deletion
        response = await ac.get(f"/api/workflows/memories/{project_key}")
        assert response.status_code == 404
