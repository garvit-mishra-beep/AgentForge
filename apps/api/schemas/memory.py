"""
ProjectMemory schemas.

Pydantic models for memory endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    """
    ProjectMemory creation schema.
    """

    project_key: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique project identifier/key",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed description of the project memory",
    )
    architecture: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plan and architecture JSON payload",
    )
    code_artifacts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Generated code files and metadata list",
    )

    model_config = dict(
        json_schema_extra={
            "example": {
                "project_key": "todo-app",
                "description": "FastAPI and React based Todo app with JWT authentication",
                "architecture": {
                    "objective": "Build a Todo App",
                    "phases": [
                        {"name": "Setup", "description": "Database schema", "estimated_hours": 3}
                    ]
                },
                "code_artifacts": [
                    {
                        "name": "README.md",
                        "type": "readme",
                        "content": "# Todo App"
                    }
                ]
            }
        }
    )


class MemoryUpdate(BaseModel):
    """
    ProjectMemory update schema.
    """

    description: Optional[str] = Field(None, description="Detailed description of the project memory")
    architecture: Optional[Dict[str, Any]] = Field(None, description="Plan and architecture JSON payload")
    code_artifacts: Optional[List[Dict[str, Any]]] = Field(None, description="Generated code files and metadata list")

    model_config = dict(
        json_schema_extra={
            "example": {
                "description": "Updated Todo App description",
            }
        }
    )


class MemoryResponse(BaseModel):
    """
    ProjectMemory response schema.
    """

    id: str
    project_key: str
    description: str
    architecture: Dict[str, Any]
    code_artifacts: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = dict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "mem-12345678-abcd",
                "project_key": "todo-app",
                "description": "FastAPI and React based Todo app with JWT authentication",
                "architecture": {
                    "objective": "Build a Todo App",
                },
                "code_artifacts": [
                    {
                        "name": "README.md",
                        "type": "readme",
                        "content": "# Todo App"
                    }
                ],
                "created_at": "2026-06-10T23:00:00",
                "updated_at": "2026-06-10T23:00:00",
            }
        }
    )
