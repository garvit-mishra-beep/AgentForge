from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: str = ""
    environment: str = ""
    version: str = ""


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    llm_config: dict = Field(default_factory=lambda: {"provider": "openai", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 4096})
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    memory_config: dict = Field(default_factory=lambda: {"type": "short_term", "turns": 20})


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    llm_config: Optional[dict] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    memory_config: Optional[dict] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    llm_config: dict
    system_prompt: Optional[str] = None
    tools: List[str]
    memory_config: dict
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    definition: dict = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[dict] = None
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    definition: dict
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionCreate(BaseModel):
    input: dict = Field(default_factory=dict)


class ExecutionStep(BaseModel):
    node: str
    llm_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: int = 0
    tool_calls: List[dict] = Field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    agent_id: Optional[uuid.UUID] = None
    workflow_id: Optional[uuid.UUID] = None
    input: Optional[dict] = None
    output: Optional[dict] = None
    status: str
    steps: List[ExecutionStep] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InvokeResponse(BaseModel):
    execution_id: uuid.UUID
    status: str = "completed"
    output: Any = None
    tokens_used: int = 0
    duration_ms: int = 0
