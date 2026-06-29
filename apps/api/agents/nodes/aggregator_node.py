import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def aggregator_node(state: AgentState) -> AgentState:
    """Aggregate results from parallel agents (reviewer, tester, security, architect)."""
    logger.info("Aggregator phase â€” combining parallel outputs")

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    if "aggregator" not in state["team_config"]:
        logger.info("No aggregator configured â€” auto-combining outputs")
        state["aggregator_output"] = _auto_aggregate(state)
        state["current_step"] = "team_lead_deliver"
        state["messages"].append({
            "role": "aggregator",
            "model": "auto",
            "content": state["aggregator_output"] or "",
            "message_type": "aggregator",
            "metadata": {"auto_aggregated": True},
        })
        return state

    # Get the model for the aggregator
    model = state["team_config"]["aggregator"]["model"]

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

    timeout_s = settings.agent_timeout.get("aggregator", 25)
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    env = load_prompt_template("aggregator.jinja2")
    template = env.get_template("aggregator.jinja2")
    system_prompt = template.render(
        task=wrap_task(state["task"]["description"]),
        plan=state.get("plan", "No plan"),
        builder_output=state.get("builder_output", "No output"),
        review=state.get("review", "{}"),
        tester_output=state.get("tester_output", "{}"),
        security_output=state.get("security_output", "{}"),
        architect_output=state.get("architect_output", "{}"),
        repository_context=wrap_context(state.get("repository_context", "")),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, wrap_task(state["task"]["description"]),
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    state["aggregator_output"] = result.content
    state["current_step"] = "team_lead_deliver"

    state["messages"].append({
        "role": "aggregator",
        "model": model,
        "content": result.content,
        "message_type": "aggregator",
        "metadata": {
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Aggregator complete")
    return state


def _auto_aggregate(state: AgentState) -> str:
    """Fallback: combine parallel outputs into a summary without LLM call.

    Verdict is derived from the *validated* ``ReviewOutput.verdict`` field of each
    source (not a substring search for "fail", TOP_FINDINGS #19). If any reviewer
    fails or surfaces a blocking finding, the overall verdict fails; if a source
    can't be parsed we conservatively require human review.
    """
    from agents.utils import parse_structured
    from models.agent_outputs import ReviewOutput, Verdict

    parts = {
        "review": state.get("review", "{}"),
        "tester_output": state.get("tester_output", "{}"),
        "security_output": state.get("security_output", "{}"),
        "architect_output": state.get("architect_output", "{}"),
    }

    verdicts: list[str] = []
    all_findings: list[dict] = []
    overall = Verdict.passed
    for key, val in parts.items():
        review = parse_structured(val or "{}", ReviewOutput)
        if review is None:
            verdicts.append(f"{key}: unparseable")
            if overall != Verdict.failed:
                overall = Verdict.review_needed
            continue
        verdicts.append(f"{key}: {review.verdict.value}")
        all_findings.extend(f.model_dump() for f in review.findings)
        if review.verdict == Verdict.failed or review.blocking:
            overall = Verdict.failed
        elif review.verdict == Verdict.review_needed and overall == Verdict.passed:
            overall = Verdict.review_needed

    return json.dumps({
        "sources": list(parts.keys()),
        "verdicts": verdicts,
        "findings": all_findings,
        "summary": f"Aggregated {len(verdicts)} outputs, {len(all_findings)} findings",
        "overall_verdict": overall.value,
    })
