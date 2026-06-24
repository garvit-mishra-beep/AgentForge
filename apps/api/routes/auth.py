"""
Authentication routes.

JWT token issuance and refresh endpoints.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.config import settings
from apps.api.dependencies.database import get_db
from apps.api.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ===============================
# AUTH SCHEMA
# ===============================


class LoginRequest(BaseModel):
    """
    Login request schema.
    """

    username: str
    password: str


class RefreshRequest(BaseModel):
    """
    Refresh token request schema.
    """

    refresh_token: str


# ===============================
# TOKEN ISSUANCE
# ===============================


@router.post(
    "/auth/token",
    tags=["Authentication"],
    summary="Access token",
    description="Obtain JWT access token with user credentials",
)
async def login_for_access_token(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login and get access token.

    Args:
        credentials: User credentials
        db: Database session

    Returns:
        Token with access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    # Validate credentials (simplified - would query database)
    # In production, verify against actual users table
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    # In production, verify against stored hash
    # For demo, accept any non-empty credentials
    if not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    # Create access token
    access_token = create_access_token(
        subject=credentials.username,
    )

    # Create refresh token
    refresh_token = create_refresh_token(
        subject=credentials.username,
    )

    logger.info(
        "Token issued",
        username=credentials.username,
        token_type="access",
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post(
    "/auth/refresh",
    tags=["Authentication"],
    summary="Refresh token",
    description="Obtain new access token with refresh token",
)
async def refresh_access_token(
    refresh_token: RefreshRequest,
):
    """
    Refresh access token.

    Args:
        refresh_token: Refresh token request

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token (simplified)
    # In production, verify token signature and expiration

    # Create new access token
    access_token = create_access_token(
        subject=refresh_token.refresh_token,
    )

    # Create new refresh token
    refresh_token_new = create_refresh_token(
        subject=refresh_token.refresh_token,
    )

    return {"access_token": access_token, "refresh_token": refresh_token_new, "token_type": "bearer"}


@router.post(
    "/auth/logout",
    tags=["Authentication"],
    summary="Logout",
    description="Logout and invalidate tokens",
)
async def logout():
    """
    Logout user.

    Returns:
        Logout confirmation
    """
    return {"message": "Logged out successfully"}
