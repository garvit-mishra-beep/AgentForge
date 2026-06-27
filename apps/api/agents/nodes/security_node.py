import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def security_node(state: AgentState) -> AgentState:
    logger.info("Security review phase")

    if "security" not in state["team_config"]:
        logger.info("No security agent configured — skipping")
        return {"security_output": '{"findings": [], "summary": "No security agent configured", "risk_level": "unknown"}'}

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the security agent
    model = state["team_config"]["security"]["model"]

    # Try to get user-specific provider configuration
    provider = None
    if db:
        try:
            provider, _ = await get_provider_for_user(
                model=model,
                user_id=user_id,
                project_id=project_id,
                db=db
            )
        except Exception as e:
            logger.warning("Failed to get user-specific provider, falling back to default: %s", e)
            provider = get_provider(model)
    else:
        # Fall back to default provider resolution
        provider = get_provider(model)

    timeout_s = settings.agent_timeout.get("security", 20)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("security.jinja2")
    template = env.get_template("security.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=state.get("plan", "No plan"),
        builder_output=state.get("builder_output", "No output"),
        repository_context=wrap_context(state.get("repository_context", "")),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, wrap_task(state["task"]["description"]),
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("security")
        output = '{"findings": [], "summary": "Timed out - partial security review", "risk_level": "unknown"}'
        return {"security_output": output, "timed_out_agents": timed_out}

    logger.info("Security review complete")
    return {"security_output": result.content}