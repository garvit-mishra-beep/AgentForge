import json
import logging

from agents.sanitize import wrap_context, wrap_task
from agents.state import AgentState
from agents.utils import _is_timeout, call_with_timeout, load_prompt_template
from core.config import settings
from core.providers import get_provider, get_provider_for_user

logger = logging.getLogger(__name__)


async def planner_node(state: AgentState) -> AgentState:
    logger.info("Planner phase — task: %s", state["task"]["title"])

    # Get user and project context from state (with fallbacks)
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    project_id = state.get("project_id")
    db = state.get("db")  # Database session would be passed in state in a real implementation

    # Get the model for the planner
    model = state["team_config"]["planner"]["model"]

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

    timeout_s = settings.agent_timeout["planner"]
    max_tokens = settings.max_output_tokens if settings.fast_demo_mode else None

    safe_task = wrap_task(state["task"]["description"])
    env = load_prompt_template("planner.jinja2")
    template = env.get_template("planner.jinja2")
    system_prompt = template.render(
        task=safe_task,
        team_config=json.dumps(state["team_config"], indent=2),
        repository_context=wrap_context(state.get("repository_context", "")),
        relevant_memories=wrap_context(state.get("relevant_memories", [])),
    )

    result = await call_with_timeout(
        provider, model, system_prompt, safe_task,
        timeout_s=timeout_s, max_tokens=max_tokens,
    )

    is_timed_out = _is_timeout(result)
    if is_timed_out:
        timed_out = state.get("timed_out_agents", [])
        timed_out.append("planner")
        state["timed_out_agents"] = timed_out
        state["planner_output"] = '{"requirements": [], "acceptance_criteria": [], "implementation_tasks": [], "dependencies": [], "risks": []}'
    else:
        state["planner_output"] = result.content

    state["current_step"] = "architect"
    state["messages"].append({
        "role": "planner",
        "model": model,
        "content": result.content,
        "message_type": "plan",
        "metadata": {
            "parsed_plan": parse_json_output(result.content) if not is_timed_out else {},
            "token_usage": result.token_usage,
            "duration_ms": result.duration_ms,
        },
    })

    logger.info("Planner phase complete")
    return state


def parse_json_output(text: str) -> dict:
    """Attempt to parse JSON from the model's output."""
    try:
        # Try to find JSON object in the text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
        return {}
    except json.JSONDecodeError:
        return {}