"""
Workflow schemas.

Pydantic models for workflow endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from enum import Enum
from pydantic import BaseModel, Field


# ===============================
# WORKFLOW STATUS
# ===============================


class WorkflowStatus(str, Enum):
    """
    Workflow status values.
    """

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RESUMING = "resuming"
    RESUMED = "resumed"
    ESCALATED = "escalated"


# =================================
# WORKFLOW SCHEMAS
# =================================


class WorkflowCreate(BaseModel):
    """
    Workflow creation schema.
    """

    workflow_id: str = Field(
        ...,
        description="Unique workflow identifier",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Workflow name",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Workflow description",
    )
    agent_type: Optional[str] = Field(
        "planner",
        description="Agent type (planner, developer, reviewer, supervisor)",
    )
    inputs: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Workflow input parameters",
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Expected output schema",
    )
    timeout_seconds: Optional[int] = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Execution timeout in seconds",
    )
    max_retries: Optional[int] = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts",
    )

    model_config = dict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf-auth-service",
                "name": "User Authentication Workflow",
                "description": "Handle user authentication and authorization",
                "agent_type": "planner",
                "inputs": {
                    "endpoint": "/api/auth/login",
                    "methods": ["POST", "GET"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "token": "string",
                        "user": "object",
                    },
                },
                "timeout_seconds": 300,
                "max_retries": 3,
            },
        },
    )


class WorkflowResponse(BaseModel):
    """
    Workflow response schema.
    """

    id: str
    workflow_id: str
    name: str
    description: Optional[str] = None
    status: WorkflowStatus
    execution_id: Optional[str] = None
    agent_type: str
    inputs: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    creator_id: Optional[str] = None

    model_config = dict(
        json_schema_extra={
            "example": {
                "id": "wf-20240101000000",
                "workflow_id": "wf-auth-service",
                "name": "User Authentication Workflow",
                "description": "Handle user authentication",
                "status": "created",
                "execution_id": "ex-20240101000000",
                "agent_type": "planner",
                "inputs": {
                    "endpoint": "/api/auth/login",
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "token": "string",
                    },
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "creator_id": "user-1",
            },
        },
    )


class WorkflowUpdate(BaseModel):
    """
    Workflow update schema.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None


# =================================
# EXECUTION SCHEMAS
# =================================


class ExecutionCreate(BaseModel):
    """
    Execution creation schema.
    """

    priority: Optional[int] = Field(
        default=5,
        ge=1,
        le=10,
        description="Execution priority (1-10)",
    )
    cancel_on_timeout: Optional[bool] = Field(
        default=True,
        description="Cancel execution on timeout",
    )
    webhook_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="Webhook URL for events",
    )

    model_config = dict(
        json_schema_extra={
            "example": {
                "priority": 5,
                "cancel_on_timeout": True,
                "webhook_url": "http://localhost:3000/webhook",
            },
        },
    )


class ExecutionResponse(BaseModel):
    """
    Execution response schema.
    """

    id: str
    workflow_id: str
    status: str
    priority: Optional[int] = None
    cancel_on_timeout: Optional[bool] = None
    webhook_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[str] = None
    checkpoint: Optional[str] = None

    model_config = dict(
        json_schema_extra={
            "example": {
                "id": "ex-20240101000000",
                "workflow_id": "wf-auth-service",
                "status": "running",
                "priority": 5,
                "cancel_on_timeout": True,
                "webhook_url": "http://localhost:3000/webhook",
                "created_at": "2024-01-01T00:00:00",
                "started_at": "2024-01-01T00:01:00",
                "completed_at": None,
                "error": None,
                "result": "{}",
                "checkpoint": "{}",
            },
        },
    )


class ExecutionUpdate(BaseModel):
    """
    Execution update schema.
    """

    status: Optional[str] = None
    error: Optional[str] = None
    webhook_url: Optional[str] = None


# =================================
# EXECUTION
# =================================


class WorkflowExecution(BaseModel):
    """
    Workflow execution response schema.
    """

    id: str
    workflow_id: str
    status: str
    priority: Optional[int] = None
    cancel_on_timeout: Optional[bool] = None
    webhook_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[str] = None
    checkpoint: Optional[str] = None


# =================================
# ENUM
# =================================


class Enum(str, Enum):
    """
    Base enum class.
    """

    pass
