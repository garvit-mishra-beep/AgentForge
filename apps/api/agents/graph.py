import logging

from langgraph.graph import END, StateGraph

from agents.nodes.aggregator_node import aggregator_node
from agents.nodes.architect_node import architect_node
from agents.nodes.builder_node import builder_node
from agents.nodes.reviewer_node import reviewer_node
from agents.nodes.security_node import security_node
from agents.nodes.tester_node import tester_node
from agents.nodes.team_lead_node import team_lead_deliver_node, team_lead_plan_node
from agents.state import AgentState

logger = logging.getLogger(__name__)


def _route_after_builder(state: AgentState) -> list[str]:
    """Fan out to available parallel agents after builder completes."""
    targets = ["reviewer"]
    if "tester" in state["team_config"]:
        targets.append("tester")
    if "security" in state["team_config"]:
        targets.append("security")
    if "architect" in state["team_config"]:
        targets.append("architect")
    return targets


def build_graph() -> StateGraph:
    workflow = StateGraph(state_schema=AgentState)

    # Sequential nodes
    workflow.add_node("team_lead_plan", team_lead_plan_node)
    workflow.add_node("builder", builder_node)

    # Parallel review nodes
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("security", security_node)
    workflow.add_node("architect", architect_node)

    # Aggregator and delivery
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("team_lead_deliver", team_lead_deliver_node)

    workflow.set_entry_point("team_lead_plan")

    # Sequential flow: plan → build
    workflow.add_edge("team_lead_plan", "builder")

    # Fan out: builder → parallel agents
    workflow.add_conditional_edges(
        "builder",
        _route_after_builder,
        ["reviewer", "tester", "security", "architect"],
    )

    # Fan in: all parallel agents → aggregator
    workflow.add_edge("reviewer", "aggregator")
    workflow.add_edge("tester", "aggregator")
    workflow.add_edge("security", "aggregator")
    workflow.add_edge("architect", "aggregator")

    # Delivery
    workflow.add_edge("aggregator", "team_lead_deliver")
    workflow.add_edge("team_lead_deliver", END)

    return workflow.compile()
