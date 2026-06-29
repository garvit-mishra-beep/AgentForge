import logging
from typing import Any, Callable, Type

from langgraph.graph import END, StateGraph
from langgraph.graph.graph import Branch
from langchain_core.runnables import Runnable
from langgraph.pregel import Channel

# Monkeypatch langgraph Branch to support parallel list routing
def _patched_runnable(self, input: Any) -> Runnable:
    result = self.condition(input)
    if isinstance(result, list):
        destinations = [self.ends[r] if self.ends else r for r in result]
        return Channel.write_to(*[f"{d}:inbox" if d != END else END for d in destinations])
    else:
        destination = self.ends[result] if self.ends else result
        return Channel.write_to(f"{destination}:inbox" if destination != END else END)

Branch.runnable = _patched_runnable

from langgraph.channels.binop import BinaryOperatorAggregate

class FanInChannel(BinaryOperatorAggregate):
    def __init__(self, typ: Type[Any], operator: Callable[[Any, Any], Any]) -> None:
        self.typ = typ
        self.operator = operator
        # Omit initializing self.value to ensure EmptyChannelError is raised when empty

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
    results = state.get("evidence_validation_result", {})
    if not results.get("builder", {}).get("is_valid", True):
        logger.warning("Builder evidence validation failed. Routing to delivery.")
        return ["team_lead_deliver"]

    targets = []
    if "reviewer" in state["team_config"]:
        targets.append("reviewer")
    if "tester" in state["team_config"]:
        targets.append("tester")
    if "security" in state["team_config"]:
        targets.append("security")

    if not targets:
        return ["aggregator"]
    return targets


def build_graph() -> Any:
    workflow = StateGraph(AgentState)

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

    # Conditional branching on validation gates
    def _route_after_planner_validation(state: Any) -> str:
        results = state.get("evidence_validation_result", {})
        if not results.get("planner", {}).get("is_valid", True):
            logger.warning("Planner evidence validation failed. Routing to delivery.")
            return "team_lead_deliver"
        return "architect"

    workflow.add_conditional_edges(
        "planner_evidence_validation",
        _route_after_planner_validation,
        {
            "team_lead_deliver": "team_lead_deliver",
            "architect": "architect",
        }
    )

    workflow.add_edge("architect", "architect_evidence_validation")

    def _route_after_architect_validation(state: Any) -> str:
        results = state.get("evidence_validation_result", {})
        if not results.get("architect", {}).get("is_valid", True):
            logger.warning("Architect evidence validation failed. Routing to delivery.")
            return "team_lead_deliver"
        return "builder"

    workflow.add_conditional_edges(
        "architect_evidence_validation",
        _route_after_architect_validation,
        {
            "team_lead_deliver": "team_lead_deliver",
            "builder": "builder",
        }
    )

    workflow.add_edge("builder", "builder_evidence_validation")

    # After builder validation, fan out to parallel agents
    workflow.add_conditional_edges(
        "builder_evidence_validation",
        _route_after_builder,
        {
            "reviewer": "reviewer",
            "tester": "tester",
            "security": "security",
            "aggregator": "aggregator",
            "team_lead_deliver": "team_lead_deliver"
        }
    )

    # Parallel execution paths with validation after each
    workflow.add_edge("reviewer", "reviewer_evidence_validation")
    workflow.add_edge("tester", "tester_evidence_validation")
    workflow.add_edge("security", "security_evidence_validation")

    # After parallel validation, check validation status before moving to aggregator
    def _route_after_parallel_validation(state: Any, role: str) -> str:
        results = state.get("evidence_validation_result", {})
        if not results.get(role, {}).get("is_valid", True):
            logger.warning("%s evidence validation failed. Routing to delivery.", role.capitalize())
            return "team_lead_deliver"
        return "aggregator"

    workflow.add_conditional_edges(
        "reviewer_evidence_validation",
        lambda s: _route_after_parallel_validation(s, "reviewer"),
        {"team_lead_deliver": "team_lead_deliver", "aggregator": "aggregator"}
    )
    workflow.add_conditional_edges(
        "tester_evidence_validation",
        lambda s: _route_after_parallel_validation(s, "tester"),
        {"team_lead_deliver": "team_lead_deliver", "aggregator": "aggregator"}
    )
    workflow.add_conditional_edges(
        "security_evidence_validation",
        lambda s: _route_after_parallel_validation(s, "security"),
        {"team_lead_deliver": "team_lead_deliver", "aggregator": "aggregator"}
    )

    # Aggregator with validation
    workflow.add_edge("aggregator", "aggregator_evidence_validation")

    def _route_after_aggregator_validation(state: Any) -> str:
        results = state.get("evidence_validation_result", {})
        if not results.get("aggregator", {}).get("is_valid", True):
            logger.warning("Aggregator evidence validation failed. Routing to delivery.")
            return "team_lead_deliver"
        return "deployment"

    workflow.add_conditional_edges(
        "aggregator_evidence_validation",
        _route_after_aggregator_validation,
        {"team_lead_deliver": "team_lead_deliver", "deployment": "deployment"}
    )

    # Deployment with validation
    workflow.add_edge("deployment", "deployment_evidence_validation")

    def _route_after_deployment_validation(state: Any) -> str:
        results = state.get("evidence_validation_result", {})
        if not results.get("deployment", {}).get("is_valid", True):
            logger.warning("Deployment evidence validation failed. Routing to delivery.")
            return "team_lead_deliver"
        return "team_lead_deliver"

    workflow.add_conditional_edges(
        "deployment_evidence_validation",
        _route_after_deployment_validation,
        {"team_lead_deliver": "team_lead_deliver"}
    )

    # Final delivery
    workflow.add_edge("team_lead_deliver", END)

    compiled = workflow.compile()

    # Enforce inbox channels that support multiple concurrent updates (fan-in) on the compiled graph
    compiled.channels["aggregator:inbox"] = FanInChannel(dict, lambda left, right: right)
    compiled.channels["team_lead_deliver:inbox"] = FanInChannel(dict, lambda left, right: right)

    # Wrap astream to default recursion_limit to 100, since our deep validation
    # graph requires more than 25 steps to execute in a single pass.
    original_astream = compiled.astream

    def patched_astream(input, config=None, **kwargs):
        if config is None:
            config = {}
        if "recursion_limit" not in config or config["recursion_limit"] < 100:
            config["recursion_limit"] = 100
        return original_astream(input, config=config, **kwargs)

    object.__setattr__(compiled, "astream", patched_astream)
    return compiled
