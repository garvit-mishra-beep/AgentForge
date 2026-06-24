"""
Common Pydantic schemas.

Shared types and base classes for API responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ===============================
# BASE SCHEMA
# ===============================


class BaseModel(BaseModel):
    """
    Base schema with common config.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        protected_namespaces=(),
    )

    class Config:
        """
        Schema configuration.
        """

        json_schema_extra = {
            "example": {
                "created_at": "2024-01-01T00:00:00",
            },
        }


# ===============================
# ID SCHEMA
# ===============================


class IdBase(BaseModel):
    """
    Base schema with ID.
    """

    id: str = Field(
        default_factory=lambda: f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        description="Resource ID",
    )


# ===============================
# TIMESTAMP SCHEMA
# ===============================


class TimestampsMixin(BaseModel):
    """
    Mixin for timestamps.
    """

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Update timestamp",
    )


# ===============================
# PAGINATION SCHEMA
# ===============================


class PaginatedResponse(BaseModel):
    """
    Pagination response wrapper.
    """

    items: list
    total: int
    limit: int
    offset: int
