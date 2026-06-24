"""
Base models for AgentOS state management.

SQLAlchemy async declarative base and mixins.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, String, Text, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr, Mapped, mapped_column

# ===============================
# DECLARATIVE BASE
# ===============================


Base = declarative_base()


# ===============================
# TIMESTAMP MIXIN
# ===============================


class TimestampMixin:
    """
    Mixin for timestamp columns.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ===============================
# UUID COLUMN
# ===============================


class GUIDMixin:
    """
    Mixin for UUID columns.
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )


# ===============================
# JSONB COLUMN
# ===============================


class JSONMixin:
    """
    Mixin for JSONB columns.
    """

    meta_data: Mapped[Dict[str, Any]] = mapped_column(
        Text,
        default=dict,
        nullable=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Get model as dictionary.
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_json(self) -> str:
        """
        Get model as JSON.
        """
        import json
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        """
        String representation.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
