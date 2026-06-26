import json
import logging

from agents.state import AgentState
from agents.utils import call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def aggregator_node(state: AgentState) -> AgentState:
    """Aggregate results from parallel agents (reviewer, tester, security, architect)."""
    logger.info("Aggregator phase — combining parallel outputs")

    if "aggregator" not in state["team_config"]:
        logger.info("No aggregator configured — auto-combining outputs")
        state["aggregator_output"] = _auto_aggregate(state)
        state["current_step"] = "team_lead_deliver"
        state["messages"].append({
            "role": "aggregator",
            "model": "auto",
            "content": state["aggregator_output"],
            "message_type": "aggregator",
            "metadata": {"auto_aggregated": True},
        })
        return state

    provider = get_provider(state["team_config"]["aggregator"]["model"])
    model = state["team_config"]["aggregator"]["model"]

    timeout_s = settings.agent_timeout.get("aggregator", 25)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("aggregator.jinja2")
    template = env.get_template("aggregator.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        plan=state.get("plan", "No plan"),
        builder_output=state.get("builder_output", "No output"),
        review=state.get("review", "{}"),
        tester_output=state.get("tester_output", "{}"),
        security_output=state.get("security_output", "{}"),
        architect_output=state.get("architect_output", "{}"),
        repository_context=state.get("repository_context", ""),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, state["task"]["description"],
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    state["aggregator_output"] = result.content
    state["current_step"] = "team_lead_deliver"

    state["messages"].append({
        "role": "aggregator",
        "model": model,
        "content": result.content,
        "message_type": "aggregator",
        "metadata": {
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Aggregator complete")
    return state


def _auto_aggregate(state: AgentState) -> str:
    """Fallback: combine parallel outputs into a summary without LLM call."""
    parts = {
        "review": state.get("review", "{}"),
        "tester_output": state.get("tester_output", "{}"),
        "security_output": state.get("security_output", "{}"),
        "architect_output": state.get("architect_output", "{}"),
    }

    verdicts = []
    for key, val in parts.items():
        try:
            data = json.loads(val) if isinstance(val, str) else val
            if isinstance(data, dict) and "verdict" in data:
                verdicts.append(f"{key}: {data['verdict']}")
            elif isinstance(data, dict) and "summary" in data:
                verdicts.append(f"{key}: {data['summary'][:100]}")
        except (json.JSONDecodeError, TypeError):
            verdicts.append(f"{key}: parsed")

    return json.dumps({
        "sources": list(parts.keys()),
        "verdicts": verdicts,
        "summary": f"Aggregated {sum(1 for v in verdicts if v)} outputs",
        "overall_verdict": "pass" if all("fail" not in v.lower() for v in verdicts) else "review_needed",
    })
