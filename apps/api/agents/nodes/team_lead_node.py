import json
import logging

from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template, parse_json_output
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def team_lead_plan_node(state: AgentState) -> AgentState:
    logger.info("Team Lead planning phase — task: %s", state["task"]["title"])

    provider = get_provider(state["team_config"]["team_lead"]["model"])
    model = state["team_config"]["team_lead"]["model"]

    timeout_s = settings.agent_timeout["team_lead_plan"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("team_lead.jinja2")
    template = env.get_template("team_lead.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        team_config=json.dumps(state["team_config"], indent=2),
        repository_context=state.get("repository_context", ""),
        relevant_memories=state.get("relevant_memories", []),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, state["task"]["description"],
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("team_lead_plan")
        state["timed_out_agents"] = timed_out
        state["plan"] = '{"plan_summary": "Timed out - partial plan", "steps": []}'
    else:
        state["plan"] = result.content

    state["current_step"] = "builder"
    state["messages"].append({
        "role": "team_lead",
        "model": model,
        "content": result.content,
        "message_type": "plan",
        "metadata": {
            "parsed_plan": parse_json_output(result.content) if not is_timed_out else {},
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Team Lead planning complete")
    return state


async def team_lead_deliver_node(state: AgentState) -> AgentState:
    logger.info("Team Lead delivery phase")

    provider = get_provider(state["team_config"]["team_lead"]["model"])
    model = state["team_config"]["team_lead"]["model"]

    timeout_s = settings.agent_timeout["team_lead_deliver"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("team_lead_deliver.jinja2")
    template = env.get_template("team_lead_deliver.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        plan=state.get("plan", ""),
        builder_output=state.get("builder_output", ""),
        review=state.get("review", ""),
        team_config=json.dumps(state["team_config"], indent=2),
        aggregator_output=state.get("aggregator_output", ""),
        repository_context=state.get("repository_context", ""),
    )

    result = await call_with_timeout(
        provider, model, system_prompt,
        "Review the team's output and prepare delivery.",
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("team_lead_deliver")
        state["timed_out_agents"] = timed_out
        state["delivery"] = '{"delivery_summary": "Delivery timed out", "verdict": "timeout"}'
    else:
        state["delivery"] = result.content

    state["current_step"] = "__end__"
    state["messages"].append({
        "role": "team_lead",
        "model": model,
        "content": result.content,
        "message_type": "delivery",
        "metadata": {
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Team Lead delivery complete")
    return state
