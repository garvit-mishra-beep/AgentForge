"""
Workflow execution state models.

SQLAlchemy models for execution state and checkpointing.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import declared_attr, Mapped, mapped_column, relationship

from packages.state.models.base import Base, TimestampMixin, GUIDMixin


# ===============================
# EXECUTION STATE MODEL
# ===============================


class ExecutionState(GUIDMixin, TimestampMixin, Base):
    """
    Execution state model.

    Represents the current state of a workflow execution.
    """

    __tablename__ = "execution_states"

    # Execution reference
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        unique=True,
        nullable=False,
        primary_key=True,
    )

    # State
    state: Mapped[str] = Column(
        String(50),
        default="init",
        nullable=False,
    )
    state_data: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )
    state_version: Mapped[int] = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # Progress
    progress: Mapped[float] = Column(
        Numeric(5, 2),
        default=0.0,
        nullable=False,
    )
    total_tasks: Mapped[int] = Column(
        Integer,
        default=0,
        nullable=False,
    )
    completed_tasks: Mapped[int] = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # Checkpoint
    checkpoint: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )


# ===============================
# CHECKPOINT MODEL
# ===============================


class Checkpoint(GUIDMixin, TimestampMixin, Base):
    """
    Checkpoint model.

    Represents a checkpoint for an execution.
    """

    __tablename__ = "execution_checkpoints"

    # Execution reference
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        nullable=False,
        index=True,
    )
    checkpoint_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        primary_key=True,
    )

    # Checkpoint state
    state_data: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )
    state_version: Mapped[int] = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # Metadata
    meta_data: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )


# ===============================
# ACTOR MODEL
# ===============================


class Actor(GUIDMixin, TimestampMixin, Base):
    """
    Actor model.

    Represents an actor (user, agent, etc.) in the execution.
    """

    __tablename__ = "actors"

    # Actor identification
    actor_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
    )
    actor_type: Mapped[str] = Column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = Column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=True,
    )
    meta_data: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )

    # State
    is_active: Mapped[bool] = Column(
        Boolean,
        default=True,
        nullable=False,
    )


# ===============================
# ACTOR-EXECUTION RELATIONSHIP
# ===============================


class ActorExecution(Base):
    """
    Actor-Execution relationship model.

    Links actors to executions.
    """

    __tablename__ = "actor_executions"

    actor_id: Mapped[str] = Column(
        String(100),
        ForeignKey("actors.actor_id"),
        primary_key=True,
        nullable=False,
    )
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        primary_key=True,
        nullable=False,
    )
    role: Mapped[str] = Column(
        String(100),
        nullable=False,
    )


# ===============================
# MESSAGE MODEL
# ===============================


class Message(GUIDMixin, TimestampMixin, Base):
    """
    Message model.

    Represents inter-agent messages.
    """

    __tablename__ = "messages"

    # Message identification
    message_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    # Sender
    sender_id: Mapped[str] = Column(
        String(100),
        ForeignKey("actors.actor_id"),
        nullable=False,
    )

    # Receiver
    receiver_id: Mapped[str] = Column(
        String(100),
        ForeignKey("actors.actor_id"),
        nullable=False,
    )

    # Execution reference
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        nullable=False,
        index=True,
    )

    # Message content
    role: Mapped[str] = Column(
        String(100),
        nullable=False,
    )
    content: Mapped[str] = Column(
        Text,
        nullable=False,
    )
    timestamp: Mapped[float] = Column(
        Numeric(16, 4),
        default=0.0,
        nullable=False,
    )


# ===============================
# OUTPUT MODEL
# ===============================


class Output(GUIDMixin, TimestampMixin, Base):
    """
    Output model.

    Represents workflow execution output.
    """

    __tablename__ = "outputs"

    # Execution reference
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        unique=True,
        nullable=False,
        primary_key=True,
    )

    # Output state
    output_data: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )
    output_schema: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )
    status: Mapped[str] = Column(
        String(50),
        default="pending",
        nullable=False,
    )


# ===============================
# METRIC MODEL
# ===============================


class Metric(GUIDMixin, TimestampMixin, Base):
    """
    Metric model.

    Tracks execution metrics.
    """

    __tablename__ = "metrics"

    # Execution reference
    execution_id: Mapped[str] = Column(
        String(100),
        ForeignKey("executions.execution_id"),
        nullable=False,
        index=True,
    )
    metric_id: Mapped[str] = Column(
        String(100),
        unique=True,
        nullable=False,
        primary_key=True,
    )

    # Metric data
    metric_name: Mapped[str] = Column(
        String(100),
        nullable=False,
    )
    value: Mapped[float] = Column(
        Numeric(10, 2),
        nullable=False,
    )
    unit: Mapped[str] = Column(
        String(50),
        nullable=True,
    )

    # Labels
    labels: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=True,
    )


# ===============================
# PROJECT MEMORY MODEL
# ===============================


import json
from sqlalchemy.types import TypeDecorator, Text

_has_vector_extension = False


class SafeVector(TypeDecorator):
    """
    TypeDecorator that falls back to Text if pgvector is not available.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim):
        self.dim = dim
        super().__init__()

    def load_dialect_impl(self, dialect):
        global _has_vector_extension
        if dialect.name == "postgresql":
            if _has_vector_extension:
                try:
                    from pgvector.sqlalchemy import Vector
                    return dialect.type_descriptor(Vector(self.dim))
                except ImportError:
                    pass
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        global _has_vector_extension
        if not _has_vector_extension:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class ProjectMemory(GUIDMixin, TimestampMixin, Base):
    """
    ProjectMemory model.

    Stores historical project descriptions, plans/architectures, and generated artifacts.
    """

    __tablename__ = "project_memories"

    project_key: Mapped[str] = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=False,
    )
    architecture: Mapped[str] = Column(
        Text,
        default="{}",
        nullable=False,
    )
    code_artifacts: Mapped[str] = Column(
        Text,
        default="[]",
        nullable=False,
    )
    embedding_data: Mapped[str] = Column(
        Text,
        nullable=True,
    )
    embedding: Mapped[list] = Column(
        SafeVector(768),
        nullable=True,
    )

