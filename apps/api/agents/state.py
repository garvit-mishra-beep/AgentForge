from typing import Any, NotRequired, TypedDict


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
    builder_output: str | None
    review: str | None
    tester_output: NotRequired[str | None]
    security_output: NotRequired[str | None]
    architect_output: NotRequired[str | None]
    aggregator_output: NotRequired[str | None]
    delivery: str | None
    current_step: str
    messages: list[AgentMessage]
    errors: list[str]
    review_attempts: NotRequired[int]
    fast_demo_mode: NotRequired[bool]
    timed_out_agents: NotRequired[list[str]]
    repository_context: NotRequired[str]
    relevant_memories: NotRequired[list[dict[str, Any]]]
