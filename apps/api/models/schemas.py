from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ProviderName(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    google = "google"
    openrouter = "openrouter"
    groq = "groq"
    ollama = "ollama"


class AgentRole(str, Enum):
    team_lead = "team_lead"
    builder = "builder"
    reviewer = "reviewer"
    tester = "tester"
    security = "security"
    architect = "architect"
    aggregator = "aggregator"


class MessageType(str, Enum):
    plan = "plan"
    code = "code"
    review = "review"
    test = "test"
    delivery = "delivery"
    error = "error"
    info = "info"
    aggregator = "aggregator"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ExecStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


# ── Auth ───────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class AuthResponse(BaseModel):
    token: str
    refresh_token: str
    user_id: str
    email: str
    name: str


# ── Teams ──────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class TeamResponse(BaseModel):
    id: UUID | str
    name: str
    description: str | None
    created_by: UUID | str
    created_at: datetime
    updated_at: datetime
    members: list["TeamMemberResponse"] = []


class TeamMemberCreate(BaseModel):
    role: AgentRole
    model: str = Field(..., min_length=1, max_length=100)


class TeamTemplateMember(BaseModel):
    role: AgentRole
    model: str = Field(..., min_length=1, max_length=100)
    instructions: str = ""


class TeamTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    use_case: str = ""
    members: list[TeamTemplateMember] = []


class TeamMemberUpdate(BaseModel):
    model: str = Field(..., min_length=1, max_length=100)


class TeamMemberResponse(BaseModel):
    id: UUID | str
    team_id: UUID | str
    role: AgentRole
    model: str
    instructions: str = ""
    created_at: datetime


# ── Tasks ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    team_id: str
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=10000)
    project_id: str | None = None


class TaskResponse(BaseModel):
    id: UUID | str
    team_id: UUID | str
    title: str
    description: str
    status: TaskStatus
    created_by: UUID | str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error_message: str | None
    project_id: UUID | str | None = None


class TaskMessageResponse(BaseModel):
    id: UUID | str
    task_id: UUID | str
    step_order: int
    role: AgentRole
    model: str
    message_type: MessageType
    content: str
    created_at: datetime


class TaskDetailResponse(TaskResponse):
    messages: list[TaskMessageResponse] = []


# ── Executions ─────────────────────────────────────────────────────────

class ExecutionResponse(BaseModel):
    id: UUID | str
    task_id: UUID | str
    status: str
    current_node: str | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


# ── API Keys ───────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    provider: ProviderName
    key: str = Field(..., min_length=1)

    @field_validator("key")
    @classmethod
    def strip_key(cls, v: str) -> str:
        return v.strip()


class ApiKeyUpdate(BaseModel):
    key: str | None = Field(None, min_length=1)
    is_enabled: bool | None = None

    @field_validator("key")
    @classmethod
    def strip_key(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class ApiKeyResponse(BaseModel):
    id: UUID | str
    provider: ProviderName
    key_preview: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class ApiKeyValidateRequest(BaseModel):
    provider: ProviderName
    key: str = Field(..., min_length=1)

    @field_validator("key")
    @classmethod
    def strip_key(cls, v: str) -> str:
        return v.strip()


class ApiKeyValidateResponse(BaseModel):
    valid: bool
    provider: ProviderName
    message: str
    format_valid: bool = False
    live_valid: bool | None = None


class ProviderInfoResponse(BaseModel):
    providers: dict


class ErrorResponse(BaseModel):
    detail: str


# ── Projects ───────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    id: UUID | str
    name: str
    description: str | None
    created_by: UUID | str
    created_at: datetime
    updated_at: datetime
    team_ids: list[UUID | str] = []


class ProjectTeamAssign(BaseModel):
    team_id: str


# ── Files ──────────────────────────────────────────────────────────────

class FileResponse(BaseModel):
    id: UUID | str
    project_id: UUID | str
    parent_id: UUID | str | None
    filename: str
    filepath: str
    mime_type: str
    size_bytes: int
    is_directory: bool
    file_hash: str | None
    status: str
    created_by: UUID | str
    created_at: datetime
    updated_at: datetime


# ── API Endpoints & Usage ──────────────────────────────────────────────

class ApiEndpointCreate(BaseModel):
    provider: ProviderName
    name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., min_length=1)
    api_key_id: str | None = None
    headers: dict | None = None
    config: dict | None = None


class ApiEndpointUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    base_url: str | None = Field(None, min_length=1)
    api_key_id: str | None = None
    is_default: bool | None = None
    headers: dict | None = None
    config: dict | None = None


class ApiEndpointResponse(BaseModel):
    id: UUID | str
    user_id: UUID | str
    project_id: UUID | str | None
    provider: str
    name: str
    base_url: str
    api_key_id: UUID | str | None
    is_default: bool
    headers: dict | None = None
    config: dict | None = None
    created_at: datetime
    updated_at: datetime


class UsageDataPoint(BaseModel):
    date: str
    cost_usd: float
    tokens: int


class UsageStatsResponse(BaseModel):
    total_cost_usd: float
    total_requests: int
    by_provider_model: list[dict]
    daily_data: list[UsageDataPoint]


# ── Code Review ────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str | None = None


class ReviewResponse(BaseModel):
    review_id: str
    status: str


class ReviewResult(BaseModel):
    review_id: str
    status: str
    baseline_issues: list[dict] | None = None
    builder_output: str | None = None
    review_issues: list[dict] | None = None
    summary: str | None = None
    model_used: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    failed_at: str | None = None


class LanguageDetectionResponse(BaseModel):
    language: str
    confidence: float
