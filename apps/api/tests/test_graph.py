"""Tests for the LangGraph agent graph with mocked AI providers."""

from unittest.mock import AsyncMock, patch

import pytest

from agents.graph import build_graph
from core.providers import ChatResponse


@pytest.fixture
def mock_providers():
    nodes = [
        "team_lead_node", "planner_node", "architect_node", "builder_node",
        "reviewer_node", "tester_node", "security_node", "aggregator_node",
        "deployment_node", "evidence_validator_node"
    ]

    async def mock_chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        if "Output JSON only" in system_prompt or "verdict" in system_prompt or "verdict" in user_message:
            return ChatResponse(content='{"summary": "mock output", "status": "ok", "verdict": "pass", "findings": []}')
        return ChatResponse(content='{"summary": "mock output", "status": "ok"}')

    patches = []
    for node in nodes:
        # Patch get_provider
        patcher = patch(f"agents.nodes.{node}.get_provider")
        mock_get_provider = patcher.start()
        provider = AsyncMock()
        provider.chat = mock_chat
        mock_get_provider.return_value = provider
        patches.append(patcher)

        # Patch get_provider_for_user with late-binding closure safety
        user_patcher = patch(f"agents.nodes.{node}.get_provider_for_user")
        mock_get_user_provider = user_patcher.start()
        def make_get_provider(p):
            async def mock_get(*args, **kwargs):
                return p, "openai"
            return mock_get
        mock_get_user_provider.side_effect = make_get_provider(provider)
        patches.append(user_patcher)

    yield

    for patcher in patches:
        patcher.stop()


def _initial_state(overrides=None):
    state = {
        "task": {
            "id": "test-1",
            "title": "Build JWT Auth",
            "description": "Create a FastAPI JWT auth module.",
        },
        "team_config": {
            "team_lead": {"role": "team_lead", "model": "gpt-4o-mini"},
            "builder": {"role": "builder", "model": "gpt-4o"},
            "reviewer": {"role": "reviewer", "model": "gpt-4o-mini"},
        },
        "plan": None,
        "builder_output": None,
        "review": None,
        "delivery": None,
        "current_step": "team_lead_plan",
        "messages": [],
        "errors": [],
    }
    if overrides:
        state.update(overrides)
    return state


@pytest.mark.asyncio
async def test_graph_completes_all_nodes(mock_providers):
    graph = build_graph()

    final_state = None
    async for event in graph.astream(_initial_state()):
        for _node_name, state_update in event.items():
            final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"
    assert len(final_state["messages"]) > 0


@pytest.mark.asyncio
async def test_graph_messages_in_order(mock_providers):
    graph = build_graph()

    final_state = None
    async for event in graph.astream(_initial_state()):
        for _node_name, state_update in event.items():
            final_state = state_update

    assert final_state is not None
    message_types = [m["message_type"] for m in final_state["messages"]]
    assert "plan" in message_types
    assert "code" in message_types
    assert "aggregator" in message_types
    assert "delivery" in message_types

    plan_idx = message_types.index("plan")
    code_idx = message_types.index("code")
    agg_idx = message_types.index("aggregator")
    del_idx = message_types.index("delivery")
    assert plan_idx < code_idx < agg_idx < del_idx


@pytest.mark.asyncio
async def test_graph_review_pass_goes_to_deliver(mock_providers):
    graph = build_graph()

    async def mock_chat_pass(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        return ChatResponse(content='{"verdict": "pass", "summary": "looks good"}')

    with patch("agents.nodes.team_lead_node.get_provider") as mock_tl, \
         patch("agents.nodes.builder_node.get_provider") as mock_b, \
         patch("agents.nodes.reviewer_node.get_provider") as mock_r:
        for m in [mock_tl, mock_b]:
            p = AsyncMock()
            p.chat = mock_chat_pass
            m.return_value = p

        rp = AsyncMock()
        rp.chat = mock_chat_pass
        mock_r.return_value = rp

        final_state = None
        async for event in graph.astream(_initial_state()):
            for _node_name, state_update in event.items():
                final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"


@pytest.mark.asyncio
async def test_graph_single_pass_always_delivers(mock_providers):
    graph = build_graph()

    async def mock_chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
        return ChatResponse(content='{"verdict": "fail", "summary": "needs work"}')

    with patch("agents.nodes.team_lead_node.get_provider") as mock_tl, \
         patch("agents.nodes.builder_node.get_provider") as mock_b, \
         patch("agents.nodes.reviewer_node.get_provider") as mock_r:
        for m in [mock_tl, mock_b]:
            p = AsyncMock()
            p.chat = mock_chat
            m.return_value = p

        rp = AsyncMock()
        rp.chat = mock_chat
        mock_r.return_value = rp

        final_state = None
        async for event in graph.astream(_initial_state()):
            for _node_name, state_update in event.items():
                final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"


@pytest.mark.asyncio
async def test_graph_byok_path(mock_providers):
    """Ensure that the graph runs successfully when db session is present, triggering the BYOK provider resolution path."""
    graph = build_graph()
    state = _initial_state({
        "db": AsyncMock(),  # Mock DB session to trigger get_provider_for_user
        "user_id": "00000000-0000-0000-0000-000000000001",
        "project_id": "00000000-0000-0000-0000-000000000002"
    })

    final_state = None
    async for event in graph.astream(state):
        for _node_name, state_update in event.items():
            final_state = state_update

    assert final_state is not None
    assert final_state["current_step"] == "__end__"
