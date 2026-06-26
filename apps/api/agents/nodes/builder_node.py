import json
import logging

from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def builder_node(state: AgentState) -> AgentState:
    logger.info("Builder phase")

    provider = get_provider(state["team_config"]["builder"]["model"])
    model = state["team_config"]["builder"]["model"]

    timeout_s = settings.agent_timeout["builder"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("builder.jinja2")
    template = env.get_template("builder.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        plan=state.get("plan", "No plan available"),
        team_config=json.dumps(state["team_config"], indent=2),
        review_feedback="",
        repository_context=state.get("repository_context", ""),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, state["task"]["description"],
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("builder")
        state["timed_out_agents"] = timed_out
        state["builder_output"] = '{"summary": "Timed out - partial code generated", "files": []}'
    else:
        state["builder_output"] = result.content

    state["current_step"] = "reviewer"
    state["messages"].append({
        "role": "builder",
        "model": model,
        "content": result.content,
        "message_type": "code",
        "metadata": {
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Builder complete")
    return state
