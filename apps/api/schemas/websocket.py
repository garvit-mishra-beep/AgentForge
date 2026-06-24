"""
WebSocket schemas.

Pydantic models for websocket events and requests.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ===============================
# SUBSCRIBE SCHEMAS
# ===============================


class SubscribeRequest(BaseModel):
    """
    Subscribe request schema.
    """

    workflow_id: str = Field(
        ...,
        description="Workflow ID to subscribe to",
    )
    event_types: Optional[List[str]] = Field(
        default=["*"],
        description="Event types to subscribe to (* for all)",
    )
    heartbeat: bool = Field(
        default=True,
        description="Enable heartbeat pings",
    )
    heartbeat_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Heartbeat interval in seconds",
    )

    model_config = dict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf-auth-service",
                "event_types": ["*"],
                "heartbeat": True,
                "heartbeat_interval": 30,
            },
        },
    )


class UnsubscribeRequest(BaseModel):
    """
    Unsubscribe request schema.
    """

    workflow_id: str = Field(
        ...,
        description="Workflow ID to unsubscribe from",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Unsubscribe reason",
    )

    model_config = dict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf-auth-service",
                "reason": "Manual unsubscribe",
            },
        },
    )


# ===============================
# EVENT SCHEMAS
# ===============================


class EventData(BaseModel):
    """
    Websocket event data schema.
    """

    event_type: str
    workflow_id: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None


class WorkflowEvent(BaseModel):
    """
    Workflow event schema.
    """

    event_type: Literal[
        "workflow.created",
        "workflow.started",
        "workflow.completed",
        "workflow.failed",
        "workflow.cancelled",
        "workflow.escalated",
        "task.started",
        "task.completed",
        "task.failed",
        "task.escalated",
    ]
    workflow_id: str
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderEvent(BaseModel):
    """
    Provider event schema.
    """

    event_type: Literal[
        "provider.request",
        "provider.response",
        "provider.error",
        "provider.timeout",
    ]
    provider: str
    model: Optional[str] = None
    status: Optional[str] = None
    tokens: Optional[Dict[str, int]] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class RetryEvent(BaseModel):
    """
    Retry event schema.
    """

    event_type: Literal[
        "retry.started",
        "retry.completed",
        "retry.failed",
        "retry.exhausted",
    ]
    workflow_id: str
    execution_id: str
    attempt: int
    error: Optional[str] = None
    success: Optional[bool] = None


class EscalationEvent(BaseModel):
    """
    Escalation event schema.
    """

    event_type: Literal[
        "escalation.started",
        "escalation.completed",
        "escalation.failed",
    ]
    workflow_id: str
    execution_id: str
    escalation_level: int
    reason: Optional[str] = None
    recommendation: Optional[str] = None


# ===============================
# MESSAGE SCHEMAS
# ===============================


class HeartbeatData(BaseModel):
    """
    Heartbeat message data.
    """

    type: Literal["ping", "pong"]
    timestamp: datetime
    workflow_id: str
    connected_clients: int


class ConnectMessage(BaseModel):
    """
    Connect message.
    """

    type: Literal["connect"]
    client_id: Optional[str] = None
    user_id: Optional[str] = None


class ErrorMessage(BaseModel):
    """
    Error message.
    """

    type: Literal["error"]
    error_code: str
    message: str
    workflow_id: Optional[str] = None
    timestamp: datetime


# ===============================
# ROOT MESSAGE TYPE
# ===============================


class RootMessage(BaseModel):
    """
    Root message type discriminator.
    """

    pass
