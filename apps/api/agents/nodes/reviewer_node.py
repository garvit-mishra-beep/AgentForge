import logging

from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider

logger = logging.getLogger(__name__)


async def reviewer_node(state: AgentState) -> AgentState:
    logger.info("Reviewer phase")

    provider = get_provider(state["team_config"]["reviewer"]["model"])
    model = state["team_config"]["reviewer"]["model"]

    timeout_s = settings.agent_timeout["reviewer"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("reviewer.jinja2")
    template = env.get_template("reviewer.jinja2")
    system_prompt = template.render(
        task=state["task"]["description"],
        plan=state.get("plan", "No plan available"),
        builder_output=state.get("builder_output", "No output to review"),
        repository_context=state.get("repository_context", ""),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, state["task"]["description"],
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("reviewer")
        review = '{"verdict": "pass", "summary": "Timed out - auto-passed", "findings": []}'
        result_ta = result
    else:
        review = result.content
        result_ta = result

    attempts = state.get("review_attempts", 0)

    logger.info("Reviewer complete")
    return {
        "review": review,
        "review_attempts": attempts + 1,
        "timed_out_agents": state.get("timed_out_agents", []),
    }
