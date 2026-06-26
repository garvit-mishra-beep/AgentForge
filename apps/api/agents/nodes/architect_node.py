import logging

from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def architect_node(state: AgentState) -> AgentState:
    logger.info("Architect review phase")

    if "architect" not in state["team_config"]:
        logger.info("No architect agent configured — skipping")
        return {"architect_output": '{"recommendations": [], "summary": "No architect agent configured", "quality_score": 0}'}

    provider = get_provider(state["team_config"]["architect"]["model"])
    model = state["team_config"]["architect"]["model"]

    timeout_s = settings.agent_timeout.get("architect", 20)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("architect.jinja2")
    template = env.get_template("architect.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        plan=state.get("plan", "No plan"),
        builder_output=state.get("builder_output", "No output"),
        repository_context=state.get("repository_context", ""),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, state["task"]["description"],
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("architect")
        output = '{"recommendations": [], "summary": "Timed out - partial review", "quality_score": 0}'
        return {"architect_output": output, "timed_out_agents": timed_out}

    logger.info("Architect review complete")
    return {"architect_output": result.content}
