import logging

from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def tester_node(state: AgentState) -> AgentState:
    logger.info("Tester phase")

    if "tester" not in state["team_config"]:
        logger.info("No tester configured — skipping")
        return {"tester_output": '{"tests": [], "summary": "No tester agent configured"}'}

    provider = get_provider(state["team_config"]["tester"]["model"])
    model = state["team_config"]["tester"]["model"]

    timeout_s = settings.agent_timeout.get("tester", 20)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("tester.jinja2")
    template = env.get_template("tester.jinja2")
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
        timed_out.append("tester")
        output = '{"tests": [], "summary": "Timed out - partial test plan", "coverage": 0}'
        return {"tester_output": output, "timed_out_agents": timed_out}

    logger.info("Tester complete")
    return {"tester_output": result.content}
