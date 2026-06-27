import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def architect_node(state: AgentState) -> AgentState:
    logger.info("Architect review phase")

    if "architect" not in state["team_config"]:
        logger.info("No architect agent configured — skipping")
        return {"architect_output": '{"recommendations": [], "summary": "No architect agent configured", "quality_score": 0}'}

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the architect
    model = state["team_config"]["architect"]["model"]

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

    timeout_s = settings.agent_timeout.get("architect", 20)
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

    # Handle case where builder_output might be a string that needs parsing
    builder_output = state.get("builder_output", "")
    if isinstance(builder_output, str) and builder_output.strip():
        try:
            # Try to parse as JSON if it looks like JSON
            if builder_output.strip().startswith('{'):
                parsed_output = json.loads(builder_output)
                builder_output_str = json.dumps(parsed_output, indent=2)
            else:
                builder_output_str = builder_output
        except json.JSONDecodeError:
            builder_output_str = builder_output
    else:
        builder_output_str = "No builder output available"

    env = load_prompt_template("architect.jinja2")
    template = env.get_template("architect.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=plan_str,
        builder_output=builder_output_str,
        repository_content=wrap_context(state.get("repository_context", "")),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, "",
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("architect")
        architect_output = '{"recommendations": [], "summary": "Timed out - no feedback provided", "quality_score": 0}'
    else:
        architect_output = result.content

    # Add to agent outputs
    current_outputs = state.get("architect_output", "")
    if isinstance(current_outputs, str) and current_outputs.strip():
        try:
            # Try to merge with existing output if it's JSON
            if current_outputs.strip().startswith('{'):
                current_data = json.loads(current_outputs)
                new_data = json.loads(architect_output)
                # Merge logic would go here
                combined_output = json.dumps({**current_data, **new_data})
            else:
                combined_output = architect_output
        except (json.JSONDecodeError, TypeError):
            combined_output = architect_output
    else:
        combined_output = architect_output

    state["architect_output"] = combined_output

    logger.info("Architect review complete")
    return state