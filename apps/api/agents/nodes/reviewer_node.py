import logging
from typing import Any

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user
from models.agent_outputs import ReviewOutput, Verdict

logger = logging.getLogger(__name__)


async def reviewer_node(state: AgentState) -> dict[str, Any]:
    logger.info("Reviewer phase")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the reviewer
    model = state["team_config"]["reviewer"]["model"]

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

    timeout_s = settings.agent_timeout["reviewer"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    # Handle tester_output - provide default if None or invalid
    tester_output_raw = state.get("tester_output")
    if tester_output_raw is None:
        # No test results yet - create a neutral default
        default_tester_result = ReviewOutput(
            verdict=Verdict.review_needed,
            summary="No test results available",
            findings=[]
        )
        tester_output_str = default_tester_result.model_dump_json()
    else:
        tester_output_str = tester_output_raw

    env = load_prompt_template("reviewer.jinja2")
    template = env.get_template("reviewer.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=state.get("plan", "No plan available"),
        builder_output=state.get("builder_output", "No output to review"),
        repository_context=wrap_context(state.get("repository_context", "")),
        learned_signal=state.get("learned_signal", ""),
        tester_output=tester_output_str,  # Include test results
    )

    result = await call_with_timeout(
        provider, model, system_prompt, wrap_task(state["task"]["description"]),
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("reviewer")
        review = '{"verdict": "pass", "summary": "Timed out - auto-passed", "findings": []}'
    else:
        review = result.content

    attempts = state.get("review_attempts", 0)

    logger.info("Reviewer complete")
    return {
        "review": review,
        "review_attempts": attempts + 1,
        "timed_out_agents": state.get("timed_out_agents", []),
    }
