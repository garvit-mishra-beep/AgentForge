"""
Workflow models.

SQLAlchemy models for workflow definitions and state.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Text as TextType
from sqlalchemy.orm import declared_attr, Mapped, mapped_column

from packages.state.models.base import Base, TimestampMixin, GUIDMixin


# ===============================
# WORKFLOW MODEL
# ===============================


class Workflow(GUIDMixin, TimestampMixin, Base):
    """
    Workflow model.

    Represents a workflow definition.
    """

    __tablename__ = "workflows"

    # Workflow identification
    workflow_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = Column(
        String(200),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=True,
    )

    # Agent type
    agent_type: Mapped[str] = Column(
        String(50),
        default="planner",
        nullable=False,
    )

    # Input/output schemas
    inputs: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )
    output_schema: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )

    # Execution settings
    timeout_seconds: Mapped[int] = Column(
        Integer,
        default=3600,
        nullable=False,
    )
    max_retries: Mapped[int] = Column(
        Integer,
        default=3,
        nullable=False,
    )

    # Status
    status: Mapped[str] = Column(
        String(50),
        default="created",
        nullable=False,
    )

    # Creator
    creator_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )


# ===============================
# EXECUTION MODEL
# ===============================


class Execution(GUIDMixin, TimestampMixin, Base):
    """
    Execution model.

    Represents a workflow execution.
    """

    __tablename__ = "executions"

    # Workflow reference
    workflow_id: Mapped[str] = Column(
        String(100),
        ForeignKey("workflows.workflow_id"),
        nullable=False,
        index=True,
    )

    # Execution identification
    execution_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # Execution state
    status: Mapped[str] = Column(
        String(50),
        default="pending",
        nullable=False,
    )
    priority: Mapped[int] = Column(
        Integer,
        default=5,
        nullable=False,
    )
    cancel_on_timeout: Mapped[bool] = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    webhook_url: Mapped[str] = Column(
        String(1000),
        nullable=True,
    )

    # Execution state
    started_at: Mapped[datetime] = Column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime] = Column(
        DateTime,
        nullable=True,
    )
    error: Mapped[str] = Column(
        Text,
        nullable=True,
    )
    result: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )

    # Checkpoint
    checkpoint: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )


# ===============================
# TASK MODEL
# ===============================


class Task(GUIDMixin, TimestampMixin, Base):
    """
    Task model.

    Represents a workflow task.
    """

    __tablename__ = "tasks"

    # Workflow reference
    workflow_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        nullable=False,
        index=True,
    )

    # Task identification
    task_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    task_name: Mapped[str] = Column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=True,
    )

    # Task state
    status: Mapped[str] = Column(
        String(50),
        default="pending",
        nullable=False,
    )
    agent: Mapped[str] = Column(
        String(50),
        default="developer",
        nullable=False,
    )
    retry_count: Mapped[int] = Column(
        Integer,
        default=0,
        nullable=False,
    )
    max_retries: Mapped[int] = Column(
        Integer,
        default=3,
        nullable=False,
    )

    # Task state
    started_at: Mapped[datetime] = Column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime] = Column(
        DateTime,
        nullable=True,
    )
    result: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )
    error: Mapped[str] = Column(
        Text,
        nullable=True,
    )


# ===============================
# EVENT LOG MODEL
# ===============================


class EventLog(GUIDMixin, TimestampMixin, Base):
    """
    Event log model.

    Records workflow execution events.
    """

    __tablename__ = "event_logs"

    # Execution reference
    workflow_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        nullable=False,
        index=True,
    )

    # Event identification
    event_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = Column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = Column(
        String(50),
        default="info",
        nullable=False,
    )

    # Event data
    data: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )

    # Related
    related_id: Mapped[str] = Column(
        String(100),
        nullable=True,
    )
    related_type: Mapped[str] = Column(
        String(50),
        nullable=True,
    )

    # Checkpoint
    checkpoint: Mapped[str] = Column(
        TextType,
        default="{}",
        nullable=True,
    )
