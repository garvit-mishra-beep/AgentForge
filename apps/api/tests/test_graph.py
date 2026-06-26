"""Tests for the LangGraph agent graph with mocked AI providers."""

from unittest.mock import AsyncMock, patch

import pytest

from agents.graph import build_graph
from core.providers import ChatResponse


@pytest.fixture
def mock_providers():
    with patch("agents.nodes.team_lead_node.get_provider") as mock_tl, \
         patch("agents.nodes.builder_node.get_provider") as mock_b, \
         patch("agents.nodes.reviewer_node.get_provider") as mock_r:

        async def mock_chat(model, system_prompt, user_message, max_tokens=None, timeout_s=None):
            return ChatResponse(content='{"summary": "mock output", "status": "ok"}')

        for m in [mock_tl, mock_b, mock_r]:
            provider = AsyncMock()
            provider.chat = mock_chat
            m.return_value = provider

        yield


def _initial_state(overrides=None):
    state = {
        "task": {
            "id": "test-1",
            "title": "Build JWT Auth",
            "description": "Create a FastAPI JWT auth module.",
        },
        "team_config": {
            "team_lead": {"role": "team_lead", "model": "qwen2.5-coder:7b"},
            "builder": {"role": "builder", "model": "qwen2.5-coder:3b"},
            "reviewer": {"role": "reviewer", "model": "dolphin-phi:latest"},
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
    assert len(final_state["messages"]) == 4


@pytest.mark.asyncio
async def test_graph_messages_in_order(mock_providers):
    graph = build_graph()

    final_state = None
    async for event in graph.astream(_initial_state()):
        for _node_name, state_update in event.items():
            final_state = state_update

    assert final_state is not None
    roles = [m["role"] for m in final_state["messages"]]
    assert roles == ["team_lead", "builder", "aggregator", "team_lead"]
    message_types = [m["message_type"] for m in final_state["messages"]]
    assert message_types == ["plan", "code", "aggregator", "delivery"]


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
