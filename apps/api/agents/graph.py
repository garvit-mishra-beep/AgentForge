import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.nodes.aggregator_node import aggregator_node
from agents.nodes.architect_node import architect_node
from agents.nodes.builder_node import builder_node
from agents.nodes.deployment_node import deployment_node
from agents.nodes.evidence_validator_node import evidence_validator_node
from agents.nodes.planner_node import planner_node
from agents.nodes.reviewer_node import reviewer_node
from agents.nodes.security_node import security_node
from agents.nodes.team_lead_node import team_lead_deliver_node, team_lead_plan_node
from agents.nodes.tester_node import tester_node
from agents.state import AgentState

logger = logging.getLogger(__name__)


def _route_after_builder(state: Any) -> list[Any]:
    """Route to appropriate validation nodes after builder completes."""
    targets = []
    if "reviewer" in state["team_config"]:
        targets.append("reviewer")
    if "tester" in state["team_config"]:
        targets.append("tester")
    if "security" in state["team_config"]:
        targets.append("security")
    return targets


def build_graph() -> Any:
    workflow = StateGraph(state_schema=AgentState)

    # Core sequence with evidence validation checkpoints
    workflow.add_node("team_lead_plan", team_lead_plan_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("planner_evidence_validation", evidence_validator_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("architect_evidence_validation", evidence_validator_node)
    workflow.add_node("builder", builder_node)
    workflow.add_node("builder_evidence_validation", evidence_validator_node)

    # Parallel validation nodes (each with their own evidence validation)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("reviewer_evidence_validation", evidence_validator_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("tester_evidence_validation", evidence_validator_node)
    workflow.add_node("security", security_node)
    workflow.add_node("security_evidence_validation", evidence_validator_node)

    # Aggregator and its validation
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("aggregator_evidence_validation", evidence_validator_node)

    # Deployment and its validation
    workflow.add_node("deployment", deployment_node)
    workflow.add_node("deployment_evidence_validation", evidence_validator_node)

    # Final team lead delivery
    workflow.add_node("team_lead_deliver", team_lead_deliver_node)

    workflow.set_entry_point("team_lead_plan")

    # Sequential flow with validation checkpoints
    workflow.add_edge("team_lead_plan", "planner")
    workflow.add_edge("planner", "planner_evidence_validation")
    workflow.add_edge("planner_evidence_validation", "architect")
    workflow.add_edge("architect", "architect_evidence_validation")
    workflow.add_edge("architect_evidence_validation", "builder")
    workflow.add_edge("builder", "builder_evidence_validation")

    # After builder validation, fan out to parallel agents
    workflow.add_conditional_edges(
        "builder_evidence_validation",
        _route_after_builder,
        ["reviewer", "tester", "security"]
    )

    # Parallel execution paths with validation after each
    workflow.add_edge("reviewer", "reviewer_evidence_validation")
    workflow.add_edge("tester", "tester_evidence_validation")
    workflow.add_edge("security", "security_evidence_validation")

    # After parallel validation, all go to aggregator
    workflow.add_edge("reviewer_evidence_validation", "aggregator")
    workflow.add_edge("tester_evidence_validation", "aggregator")
    workflow.add_edge("security_evidence_validation", "aggregator")

    # Aggregator with validation
    workflow.add_edge("aggregator", "aggregator_evidence_validation")
    workflow.add_edge("aggregator_evidence_validation", "deployment")

    # Deployment with validation
    workflow.add_edge("deployment", "deployment_evidence_validation")
    workflow.add_edge("deployment_evidence_validation", "team_lead_deliver")

    # Final delivery
    workflow.add_edge("team_lead_deliver", END)

    return workflow.compile()
