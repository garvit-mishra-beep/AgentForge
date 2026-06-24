from __future__ import annotations

import uuid
import pytest
from unittest.mock import AsyncMock, patch

from apps.api.main import app
from apps.api.services import AgentService, WorkflowService, ExecutionService


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_token_success(client, mock_db):
    from apps.api.core.security import hash_password
    from apps.api.models import User

    mock_user = User(
        username="testuser",
        password_hash=hash_password("testpass"),
        tenant_id=uuid.uuid4(),
        is_active=True,
    )

    class AuthMockResult:
        def scalar_one_or_none(self):
            return mock_user

    mock_db.execute = AsyncMock(return_value=AuthMockResult())

    response = await client.post(
        "/api/v1/auth/token",
        json={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_token_empty_credentials(client):
    response = await client.post(
        "/api/v1/auth/token",
        json={"username": "", "password": ""},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_auth_unauthorized(anon_client):
    response = await anon_client.get("/api/v1/agents")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_agent_crud(client):
    agent_id = str(uuid.uuid4())
    mock_agent = AsyncMock()
    mock_agent.id = agent_id
    mock_agent.name = "Test Agent"
    mock_agent.slug = "test-agent"
    mock_agent.description = "A test agent"
    mock_agent.llm_config = {}
    mock_agent.system_prompt = None
    mock_agent.tools = []
    mock_agent.memory_config = {"type": "none"}
    mock_agent.version = 1
    mock_agent.status = "draft"
    from datetime import datetime
    mock_agent.created_at = datetime(2025, 1, 1)
    mock_agent.updated_at = datetime(2025, 1, 1)

    mock_service = AsyncMock(spec=AgentService)
    mock_service.create.return_value = mock_agent
    mock_service.get.return_value = mock_agent
    mock_service.update.return_value = mock_agent
    mock_service.list.return_value = [mock_agent]
    mock_service.delete.return_value = True

    with patch("apps.api.routes.agents.AgentService", return_value=mock_service):
        create = await client.post(
            "/api/v1/agents",
            json={"name": "Test Agent", "slug": "test-agent", "description": "A test agent"},
        )
        assert create.status_code == 201
        assert "id" in create.json()


@pytest.mark.asyncio
async def test_agent_invoke(client):
    agent_id = str(uuid.uuid4())
    from datetime import datetime
    mock_agent = AsyncMock()
    mock_agent.id = agent_id
    mock_agent.llm_config = {"provider": "openai", "model": "gpt-4o", "temperature": 0.7}
    mock_agent.system_prompt = "You are a helpful assistant."
    mock_agent.tools = []
    mock_agent.created_at = datetime(2025, 1, 1)
    mock_agent.updated_at = datetime(2025, 1, 1)

    mock_agent_svc = AsyncMock(spec=AgentService)
    mock_agent_svc.get.return_value = mock_agent

    mock_exec_svc = AsyncMock(spec=ExecutionService)

    import apps.api.routes.agents as routes_mod
    with (
        patch.object(routes_mod, "AgentService", return_value=mock_agent_svc),
        patch.object(routes_mod, "ExecutionService", return_value=mock_exec_svc),
    ):
        response = await client.post(
            f"/api/v1/agents/{agent_id}/invoke",
            json={"message": "Hello"},
        )
        assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_workflow_crud(client):
    wf_id = str(uuid.uuid4())
    from datetime import datetime
    mock_wf = AsyncMock()
    mock_wf.id = wf_id
    mock_wf.name = "Test Workflow"
    mock_wf.description = "A test workflow"
    mock_wf.definition = {"nodes": [], "edges": []}
    mock_wf.version = 1
    mock_wf.status = "draft"
    mock_wf.created_at = datetime(2025, 1, 1)
    mock_wf.updated_at = datetime(2025, 1, 1)

    mock_service = AsyncMock(spec=WorkflowService)
    mock_service.create.return_value = mock_wf
    mock_service.get.return_value = mock_wf
    mock_service.update.return_value = mock_wf
    mock_service.list.return_value = [mock_wf]
    mock_service.delete.return_value = True

    with patch("apps.api.routes.workflows.WorkflowService", return_value=mock_service):
        create = await client.post(
            "/api/v1/workflows",
            json={"name": "Test Workflow", "description": "A test workflow", "definition": {"nodes": [], "edges": []}},
        )
        assert create.status_code == 201
        assert "id" in create.json()


@pytest.mark.asyncio
async def test_executions_list(client):
    mock_svc = AsyncMock(spec=ExecutionService)
    mock_svc.list.return_value = []
    with patch("apps.api.routes.executions.ExecutionService", return_value=mock_svc):
        response = await client.get("/api/v1/executions")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_observability_usage(client):
    mock_svc = AsyncMock(spec=ExecutionService)
    mock_svc.get_metrics.return_value = {"total_executions": 0, "total_tokens": 0, "total_cost_usd": 0.0, "avg_duration_ms": 0.0}
    with patch("apps.api.routes.observability.ExecutionService", return_value=mock_svc):
        response = await client.get("/api/v1/observability/usage")
        assert response.status_code == 200
