import operator
from typing import Annotated, Any, NotRequired, TypedDict


def merge_validation_results(left: dict | None, right: dict | None) -> dict:
    if left is None:
        left = {}
    if right is None:
        right = {}
    return {**left, **right}


class TaskInfo(TypedDict):
    id: str
    title: str
    description: str


class TeamMemberConfig(TypedDict):
    role: str
    model: str


class AgentMessage(TypedDict):
    role: str
    model: str
    content: str
    message_type: str
    metadata: dict[str, Any]


class AgentState(TypedDict):
    task: TaskInfo
    team_config: dict[str, TeamMemberConfig]
    plan: str | None
    planner_output: NotRequired[str | None]
    builder_output: str | None
    review: str | None
    tester_output: NotRequired[str | None]
    security_output: NotRequired[str | None]
    architect_output: NotRequired[str | None]
    deployment_output: NotRequired[str | None]
    aggregator_output: NotRequired[str | None]
    delivery: str | None
    current_step: str
    messages: Annotated[list[AgentMessage], operator.add]
    errors: list[str]
    review_attempts: NotRequired[int]
    fast_demo_mode: NotRequired[bool]
    timed_out_agents: NotRequired[list[str]]
    repository_context: NotRequired[str]
    relevant_memories: NotRequired[list[dict[str, Any]]]
    learned_signal: NotRequired[str]
    # BYOK fields - user and project context for provider selection
    user_id: NotRequired[str]
    project_id: NotRequired[str]
    # Database session (would be passed in a real implementation)
    db: NotRequired[Any]
    evidence_validation_result: Annotated[dict, merge_validation_results]
