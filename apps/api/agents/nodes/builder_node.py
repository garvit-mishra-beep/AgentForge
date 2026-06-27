import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def builder_node(state: AgentState) -> AgentState:
    logger.info("Builder phase")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the builder
    model = state["team_config"]["builder"]["model"]

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

    timeout_s = settings.agent_timeout["builder"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    # Handle case where plan might be a string that needs parsing
    plan = state.get("plan", "")
    if isinstance(plan, str) and plan.strip():
        try:
            # Try to parse as JSON if it looks like JSON
            if plan.strip().startswith('{'):
                parsed_plan = json.loads(plan)
                plan_str = json.dumps(parsed_plan, indent=2)
            else:
                plan_str = plan
        except json.JSONDecodeError:
            plan_str = plan
    else:
        plan_str = "No plan provided"

    env = load_prompt_template("builder.jinja2")
    template = env.get_template("builder.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=plan_str,
        repository_context=wrap_context(state.get("repository_context", "")),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, "",  # Note: builder_node doesn't seem to pass task to call_with_timeout in original
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