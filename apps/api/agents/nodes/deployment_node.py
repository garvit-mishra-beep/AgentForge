import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def deployment_node(state: AgentState) -> AgentState:
    logger.info("Deployment phase")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the deployment agent (fall back to team_lead model or settings default if not specified)
    model = state["team_config"].get("deployment", {}).get("model", state["team_config"].get("team_lead", {}).get("model", "qwen2.5-coder:7b"))

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

    timeout_s = settings.agent_timeout.get("deployment", 20)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    # We need to gather the outputs from previous stages: plan, planner_output, builder_output, reviewer, tester, security, architect
    # For the deployment agent, we need to validate build, CI, deployment readiness, migrations, release safety.
    # We'll pass the relevant outputs to the prompt.

    env = load_prompt_template("deployment.jinja2")
    template = env.get_template("deployment.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=state.get("plan", ""),
        planner_output=state.get("planner_output", ""),
        builder_output=state.get("builder_output", ""),
        reviewer_output=state.get("review", ""),
        tester_output=state.get("tester_output", ""),
        security_output=state.get("security_output", ""),
        architect_output=state.get("architect_output", ""),
        repository_context=wrap_context(state.get("repository_context", "")),
        team_config=json.dumps(state["team_config"], indent=2),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, "",
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("deployment")
        state["timed_out_agents"] = timed_out
        state["deployment_output"] = '{"build_status": "unknown", "lint_status": "unknown", "test_status": "unknown", "deployment_checks": [], "deployment_ready": false}'
    else:
        state["deployment_output"] = result.content

    state["current_step"] = "team_lead_deliver"
    state["messages"].append({
        "role": "deployment",
        "model": model,
        "content": result.content,
        "message_type": "deployment",
        "metadata": {
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Deployment phase complete")
    return state