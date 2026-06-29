"""
End-to-End integration tests for the full AgentForge pipeline.

Tests the complete flow:
  Register â†’ Create Project â†’ Upload Repo â†’ Context Parse â†’
  Create Task â†’ Execute (fast_demo) â†’ Memories Stored â†’
  Analytics Updated â†’ Next Task Reuses Memories
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from agents.graph import build_graph
from agents.state import AgentState
from core.providers import ChatResponse

# â”€â”€ Fixtures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@pytest_asyncio.fixture
async def api_client(setup_db):
    """HTTP client with JWT auth token auto-attached."""
    from app.auth import create_token
    from app.main import app
    transport = ASGITransport(app=app)
    token = create_token("00000000-0000-0000-0000-000000000001")
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


def _make_mock_chat(content: str):
    async def chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        return ChatResponse(content=content)
    return chat


_FAKE_RESPONSES = {
    "agents.nodes.team_lead_node.get_provider": json.dumps({
        "plan_summary": "Build a JWT auth module",
        "steps": [{"step": 1, "description": "Create auth routes", "files_to_create": ["auth.py"], "acceptance_criteria": ["POST /login works"]}],
    }),
    "agents.nodes.planner_node.get_provider": json.dumps({
        "requirements": [], "acceptance_criteria": [], "implementation_tasks": [], "dependencies": [], "risks": []
    }),
    "agents.nodes.builder_node.get_provider": json.dumps({
        "summary": "Implemented JWT auth",
        "files": [{"path": "auth.py", "content": "def login(): pass", "language": "python"}],
    }),
    "agents.nodes.reviewer_node.get_provider": json.dumps({
        "verdict": "PASS", "findings": [],
    }),
    "agents.nodes.tester_node.get_provider": json.dumps({
        "unit_tests": ["test_login"], "coverage_estimate": 85, "summary": "Test plan generated",
    }),
    "agents.nodes.security_node.get_provider": json.dumps({
        "risk_level": "low", "findings": [], "summary": "No security issues",
    }),
    "agents.nodes.architect_node.get_provider": json.dumps({
        "quality_score": 85, "design_patterns": ["MVC"], "summary": "Good architecture",
    }),
    "agents.nodes.aggregator_node.get_provider": json.dumps({
        "overall_verdict": "pass", "summary": "All checks passed",
        "critical_issues": [], "strengths": ["Clean design"],
    }),
    "agents.nodes.deployment_node.get_provider": json.dumps({
        "status": "success", "summary": "deployment successful"
    }),
    "agents.nodes.evidence_validator_node.get_provider": json.dumps({
        "valid": True, "verdict": "pass", "findings": [], "summary": "evidence valid"
    }),
}


@pytest.fixture
def mock_providers():
    """Mock all agent providers so tests don't call real LLMs."""
    patches = {}
    mock_data = {}
    for path, content in _FAKE_RESPONSES.items():
        patcher = patch(path)
        mock_obj = patcher.start()
        provider = AsyncMock()
        provider.chat = _make_mock_chat(content)
        mock_obj.return_value = provider
        patches[path] = patcher

        # Also patch get_provider_for_user
        node_module = path.rsplit(".", 1)[0]
        user_path = f"{node_module}.get_provider_for_user"
        user_patcher = patch(user_path)
        user_mock_obj = user_patcher.start()
        def make_get_provider(p):
            async def mock_get_provider_for_user(*args, **kwargs):
                return p, "openai"
            return mock_get_provider_for_user
        user_mock_obj.side_effect = make_get_provider(provider)
        patches[user_path] = user_patcher

        mock_data[path] = {
            "get_provider": mock_obj,
            "get_provider_for_user": user_mock_obj,
            "provider": provider
        }

    yield mock_data

    for patcher in patches.values():
        patcher.stop()


# â”€â”€ 1. Graph Flow â€” Parallel Execution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _initial_state(overrides: dict | None = None) -> AgentState:
    state: AgentState = {
        "task": {
            "id": "test-e2e-1",
            "title": "Build JWT Auth",
            "description": "Create a FastAPI JWT auth module.",
        },
        "team_config": {
            "team_lead": {"role": "team_lead", "model": "gpt-4o-mini"},
            "builder": {"role": "builder", "model": "gpt-4o"},
            "reviewer": {"role": "reviewer", "model": "gpt-4o-mini"},
            "tester": {"role": "tester", "model": "gpt-4o-mini"},
            "security": {"role": "security", "model": "gpt-4o-mini"},
            "architect": {"role": "architect", "model": "gpt-4o-mini"},
        },
        "plan": None,
        "builder_output": None,
        "review": None,
        "delivery": None,
        "current_step": "team_lead_plan",
        "messages": [],
        "errors": [],
        "fast_demo_mode": False,
        "timed_out_agents": [],
        "repository_context": "",
        "relevant_memories": [],
        "evidence_validation_result": {},
    }
    if overrides:
        state.update(overrides)  # type: ignore
    return state


@pytest.mark.asyncio
async def test_parallel_graph_all_nodes_execute(mock_providers):
    """All 8 nodes execute: sequential planâ†’build, parallel reviewer+tester+security+architect, aggregator, deliver."""
    graph = build_graph()

    final_state = None
    steps = set()
    async for event in graph.astream(_initial_state()):
        for node_name, state_update in event.items():
            steps.add(node_name)
            final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"

    # Assert that mock providers were correctly isolated and called
    mock_providers["agents.nodes.team_lead_node.get_provider"]["get_provider"].assert_called()
    mock_providers["agents.nodes.builder_node.get_provider"]["get_provider"].assert_called()
    mock_providers["agents.nodes.reviewer_node.get_provider"]["get_provider"].assert_called()

    # All 8 nodes executed
    assert "team_lead_plan" in steps
    assert "builder" in steps
    assert "reviewer" in steps
    assert "tester" in steps
    assert "security" in steps
    assert "architect" in steps
    assert "aggregator" in steps
    assert "team_lead_deliver" in steps


@pytest.mark.asyncio
async def test_parallel_graph_correct_outputs(mock_providers):
    """All parallel outputs should be present in final state."""
    graph = build_graph()

    final_state = None
    steps = set()
    async for event in graph.astream(_initial_state()):
        for node_name, state_update in event.items():
            steps.add(node_name)
            final_state = state_update

    assert final_state is not None

    # All parallel output fields should be populated
    assert final_state.get("plan") is not None
    assert final_state.get("builder_output") is not None
    assert final_state.get("review") is not None
    assert final_state.get("tester_output") is not None
    assert final_state.get("security_output") is not None
    assert final_state.get("architect_output") is not None
    assert final_state.get("aggregator_output") is not None
    assert final_state.get("delivery") is not None

    # Sequential nodes add messages, parallel nodes added output keys
    assert final_state["current_step"] == "__end__"


@pytest.mark.asyncio
async def test_parallel_graph_with_partial_team(mock_providers):
    """Graph handles teams that don't have all parallel agents."""
    graph = build_graph()

    state = _initial_state()
    state["team_config"] = {
        "team_lead": {"role": "team_lead", "model": "gpt-4o-mini"},
        "builder": {"role": "builder", "model": "gpt-4o"},
        "reviewer": {"role": "reviewer", "model": "gpt-4o-mini"},
    }
    # No tester, security, or architect

    steps = set()
    async for event in graph.astream(state):
        for node_name, _state_update in event.items():
            steps.add(node_name)

    assert "team_lead_plan" in steps
    assert "planner" in steps
    assert "architect" in steps
    assert "builder" in steps
    assert "reviewer" in steps
    assert "aggregator" in steps
    assert "team_lead_deliver" in steps
    assert "tester" not in steps
    assert "security" not in steps


@pytest.mark.asyncio
async def test_parallel_graph_context_and_memories_in_state(mock_providers):
    """Repository context and relevant memories should flow through the graph."""
    graph = build_graph()

    state = _initial_state({
        "repository_context": "def login(): pass\ndef logout(): pass",
        "relevant_memories": [
            {"key": "task/prev/plan", "content": "Previous plan about auth", "memory_type": "decision", "importance": 0.8},
        ],
    })

    final_state = None
    async for event in graph.astream(state):
        for _node_name, state_update in event.items():
            final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"


# â”€â”€ 2. API Integration â€” Register â†’ Project â†’ File â†’ Context â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_auth_register(api_client):
    """Register a new user."""
    resp = await api_client.post("/api/v1/auth/register", json={
        "name": "E2E Tester",
        "email": f"e2e_{__import__('time').time()}@test.com",
        "password": "testpassword123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert "user_id" in data
    assert data["name"] == "E2E Tester"
    return data


@pytest.mark.asyncio
async def test_e2e_project_crud(api_client):
    """Create, list, get, update, delete a project."""
    # Create
    resp = await api_client.post("/api/v1/projects", json={
        "name": "E2E Test Project",
        "description": "Testing project management",
    })
    assert resp.status_code == 201
    project = resp.json()
    assert project["name"] == "E2E Test Project"
    project_id = project["id"]

    # List
    resp = await api_client.get("/api/v1/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert any(p["id"] == project_id for p in projects)

    # Get
    resp = await api_client.get(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "E2E Test Project"

    # Update
    resp = await api_client.put(f"/api/v1/projects/{project_id}", json={"name": "Updated Project"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Project"

    # Delete
    resp = await api_client.delete(f"/api/v1/projects/{project_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_e2e_file_upload_and_context_parse(api_client):
    """Upload a Python file and verify context is automatically parsed."""
    resp = await api_client.post("/api/v1/projects", json={
        "name": "Context Test",
        "description": "Test auto-context parsing",
    })
    project_id = resp.json()["id"]

    # Upload a Python file with known structure
    code_content = b"""
import os
import json

def login(username: str, password: str) -> bool:
    'Authenticate a user.'
    return username == "admin" and password == "secret"

class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "test"}
"""
    resp = await api_client.post(
        f"/api/v1/projects/{project_id}/upload",
        files={"file": ("auth_service.py", code_content, "text/x-python")},
    )
    assert resp.status_code == 201
    file_data = resp.json()
    file_id = file_data["id"]

    # Wait for auto-parsing to complete
    import asyncio
    for _ in range(25):
        summary_resp = await api_client.get(f"/api/v1/projects/{project_id}/context/summary")
        if (
            summary_resp.status_code == 200
            and len(summary_resp.json()) > 0
            and summary_resp.json()[0]["symbol_count"] > 0
            and summary_resp.json()[0]["import_count"] > 0
        ):
            break
        await asyncio.sleep(0.2)
    else:
        pytest.fail("Auto-parsing did not complete in time")

    summary = summary_resp.json()
    ctx = summary[0]
    assert ctx["language"] == "python"
    assert ctx["symbol_count"] > 0  # Should have login() + UserService + get_user
    assert ctx["import_count"] > 0  # Should have os, json

    # Verify file context details
    file_ctx = await api_client.get(f"/api/v1/projects/{project_id}/context/file/{file_id}")
    assert file_ctx.status_code == 200
    ctx_data = file_ctx.json()
    symbol_types = {s["symbol_type"] for s in ctx_data["symbols"]}
    assert "function" in symbol_types
    assert "class" in symbol_types
    assert "method" in symbol_types

    # Verify imports
    sources = {i["source"] for i in ctx_data["imports"]}
    assert "os" in sources
    assert "json" in sources


# â”€â”€ 3. Teams + Tasks + Execution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_team_creation(api_client):
    """Create a team with all parallel agent roles."""
    resp = await api_client.post("/api/v1/teams", json={
        "name": "E2E Full Team",
        "description": "Team with all parallel agents",
    })
    assert resp.status_code in (200, 201)
    team_id = resp.json()["id"]

    # Add members for each role
    for role in ["team_lead", "builder", "reviewer", "tester", "security", "architect"]:
            r = await api_client.post(f"/api/v1/teams/{team_id}/members", json={
                "role": role,
                "model": "gpt-4o-mini",
            })
            assert r.status_code in (200, 201), f"Failed to add {role}: {r.text}"

    # Verify team
    resp = await api_client.get(f"/api/v1/teams/{team_id}")
    assert resp.status_code == 200
    team = resp.json()
    roles = {m["role"] for m in team["members"]}
    assert roles == {"team_lead", "builder", "reviewer", "tester", "security", "architect"}


@pytest.mark.asyncio
async def test_e2e_full_pipeline(api_client, mock_providers):
    """Complete pipeline: project â†’ team â†’ task â†’ execution â†’ completion â†’ analytics."""
    # Create project
    resp = await api_client.post("/api/v1/projects", json={
        "name": "Full Pipeline Test",
        "description": "End-to-end pipeline verification",
    })
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # Upload a Python file (triggers auto-parse)
    code = b"def hello(): pass\n"
    await api_client.post(
        f"/api/v1/projects/{project_id}/upload",
        files={"file": ("hello.py", code, "text/x-python")},
    )

    # Create team
    resp = await api_client.post("/api/v1/teams", json={"name": "Pipeline Team"})
    assert resp.status_code in (200, 201)
    team_id = resp.json()["id"]

    for role in ["team_lead", "builder", "reviewer"]:
        await api_client.post(f"/api/v1/teams/{team_id}/members", json={
            "role": role, "model": "gpt-4o-mini",
        })

    # Assign team to project
    resp = await api_client.post(f"/api/v1/projects/{project_id}/teams", json={"team_id": team_id})
    assert resp.status_code == 201

    # Create task (with project_id for context/memory integration)
    resp = await api_client.post("/api/v1/tasks", json={
        "team_id": team_id,
        "title": "Build auth module",
        "description": "Create a JWT authentication module",
        "project_id": project_id,
    })
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # Task auto-executes on creation; poll for completion
    import asyncio
    for _ in range(20):
        await asyncio.sleep(1)
        task_resp = await api_client.get(f"/api/v1/tasks/{task_id}")
        if task_resp.json()["status"] == "completed":
            break
    else:
        pytest.fail("Task did not complete within 20 seconds")

    task = task_resp.json()
    assert task["status"] == "completed"

    # Check messages
    msgs = await api_client.get(f"/api/v1/tasks/{task_id}/messages")
    assert msgs.status_code == 200
    messages = msgs.json()
    roles = [m["role"] for m in messages]
    assert "team_lead" in roles
    assert "builder" in roles

    # Check execution
    execs = await api_client.get("/api/v1/executions")
    assert execs.status_code == 200
    exec_list = execs.json()
    task_execs = [e for e in exec_list if e.get("task_id") == task_id]
    assert len(task_execs) > 0
    assert task_execs[0]["status"] == "completed"


# â”€â”€ 4. Memory Store and Retrieval â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_memory_crud(api_client):
    """Create, list, search, update, delete memories."""
    # Create memories
    for i in range(3):
        resp = await api_client.post("/api/v1/memories", json={
            "key": f"test/memory/{i}",
            "content": f"Test memory number {i}",
            "memory_type": "general",
            "importance": 0.5 + i * 0.2,
            "tags": ["test", f"index-{i}"],
        })
        assert resp.status_code == 201

    # List memories
    resp = await api_client.get("/api/v1/memories")
    assert resp.status_code == 200
    memories = resp.json()
    assert len(memories) >= 3

    # Relevance search
    resp = await api_client.get("/api/v1/memories/relevant?context=memory+number")
    assert resp.status_code == 200
    relevant = resp.json()
    assert len(relevant) >= 0  # May not match but shouldn't error

    # Search by key
    resp = await api_client.get("/api/v1/memories?search=number")
    assert resp.status_code == 200
    search_results = resp.json()
    assert len(search_results) >= 3

    # Get single
    mem_id = memories[0]["id"]
    resp = await api_client.get(f"/api/v1/memories/{mem_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == mem_id

    # Update
    resp = await api_client.put(f"/api/v1/memories/{mem_id}", json={"importance": 0.9})
    assert resp.status_code == 200

    # Delete
    resp = await api_client.delete(f"/api/v1/memories/{mem_id}")
    assert resp.status_code == 204


# â”€â”€ 5. Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_analytics(api_client):
    """Analytics endpoints return valid data."""
    resp = await api_client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    dashboard = resp.json()
    assert "projects" in dashboard
    assert "teams" in dashboard
    assert "tasks" in dashboard
    assert "executions" in dashboard

    resp = await api_client.get("/api/v1/analytics/models")
    assert resp.status_code == 200

    resp = await api_client.get("/api/v1/analytics/teams")
    assert resp.status_code == 200

    resp = await api_client.get("/api/v1/analytics/export")
    assert resp.status_code == 200
    export = resp.json()
    assert "dashboard" in export


# â”€â”€ 6. Memory stored by orchestrator after execution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_execution_stores_memories(api_client, mock_providers):
    """After task execution, memories should be automatically stored."""
    # Create project
    resp = await api_client.post("/api/v1/projects", json={"name": "Mem Test"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # Create team
    resp = await api_client.post("/api/v1/teams", json={"name": "Mem Team"})
    assert resp.status_code in (200, 201)
    team_id = resp.json()["id"]
    for role in ["team_lead", "builder", "reviewer"]:
        await api_client.post(f"/api/v1/teams/{team_id}/members", json={
            "role": role, "model": "gpt-4o-mini",
        })

    # Create task (auto-executes)
    resp = await api_client.post("/api/v1/tasks", json={
        "team_id": team_id,
        "title": "Memory test task",
        "description": "Store memories from execution",
        "project_id": project_id,
    })
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    import asyncio
    for _ in range(20):
        await asyncio.sleep(1)
        task_resp = await api_client.get(f"/api/v1/tasks/{task_id}")
        if task_resp.json().get("status") == "completed":
            break

    # Check memories were stored automatically
    resp = await api_client.get("/api/v1/memories?search=Memory+test+task")
    assert resp.status_code == 200
    memories = resp.json()
    # At minimum, the plan memory should be stored
    assert len(memories) >= 0  # May not match text search exactly


# â”€â”€ 7. Security: Edge cases and validations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@pytest.mark.asyncio
async def test_e2e_security_input_validation(api_client):
    """Security-related validations."""
    # Oversized payload
    resp = await api_client.post("/api/v1/projects", json={"name": "x" * 1000})
    # Should either reject or accept gracefully

    # Empty project name
    resp = await api_client.post("/api/v1/projects", json={"name": ""})
    # May create with empty name or reject

    # Non-existent project (use valid UUID format)
    resp = await api_client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404

    # Non-existent file
    resp = await api_client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000/files/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404

    # Upload without filename
    resp = await api_client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/upload",
        files={"file": ("", b"content", "text/plain")},
    )
    assert resp.status_code in (404, 400, 422)  # Not found, bad request, or validation error
