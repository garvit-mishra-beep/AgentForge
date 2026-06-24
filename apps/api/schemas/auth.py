"""
Authentication schemas.

Pydantic models for auth endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ===============================
# TOKEN SCHEMAS
# ===============================


class Token(BaseModel):
    """
    Token response schema.
    """

    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

    model_config = dict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            },
        },
    )


class TokenCredentials(BaseModel):
    """
    Credentials for token issuance.
    """

    username: str
    password: str

    model_config = dict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "password",
            },
        },
    )


class TokenRefresh(BaseModel):
    """
    Refresh token request schema.
    """

    refresh_token: str

    model_config = dict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            },
        },
    )


# ===============================
# USER SCHEMAS
# ===============================


class UserBase(BaseModel):
    """
    User base schema.
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    User creation schema.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 chars)",
    )


class UserResponse(BaseModel):
    """
    User response schema.
    """

    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = dict(
        json_schema_extra={
            "example": {
                "id": "1",
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Admin User",
                "is_active": True,
                "is_superuser": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
        },
    )


class UserUpdate(BaseModel):
    """
    User update schema.
    """

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    model_config = dict(
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "full_name": "New Name",
            },
        },
    )
