"""
Authentication dependencies.

Provides auth dependencies for route handlers and validators.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.core.config import settings
from apps.api.core.database import async_session, engine
from apps.api.core.security import (
    oauth2_scheme,
    verify_token,
    hash_password,
    verify_password,
    get_password_hash,
)
from apps.api.dependencies.database import get_db

logger = logging.getLogger(__name__)

# ===============================
# OAUTH2 SCHEME
# ===============================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.HOST}:{settings.PORT}/api/auth/token",
    description=f"JWT access token for {settings.APPLICATION_NAME}",
)

# ===============================
# DEPENDENCIES
# ===============================


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Any:
    """
    Get current authenticated user.

    Args:
        token: JWT access token

    Returns:
        User data or None

    Raises:
        HTTPException: If authentication fails
    """
    # Verify token
    payload = verify_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"www-authenticate": "Bearer realm="},
        )

    # Extract user ID
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Check token expiration
    if "exp" in payload:
        exp = payload["exp"]
        current = datetime.utcnow().timestamp()
        if current >= exp:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

    return {"sub": user_id, "payload": payload}


async def get_current_active_user(
    user: Any = Depends(get_current_user),
) -> Any:
    """
    Get current active user.

    Args:
        user: User from token

    Returns:
        Active user data

    Raises:
        HTTPException: If user is not active
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


async def get_current_active_superuser(
    user: Any = Depends(get_current_active_user),
) -> Any:
    """
    Get current active superuser.

    Args:
        user: User from token

    Returns:
        Superuser data

    Raises:
        HTTPException: If user is not a superuser
    """
    # Check if user is superuser
    is_superuser = user.get("payload", {}).get("is_superuser", False)

    if not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return user


# ===============================
# USER VALIDATION DEPENDENCIES
# ===============================


async def get_user_by_id(
    db: AsyncSession = Depends(get_db),
    user_id: str = "",
) -> Any:
    """
    Get user by ID from database.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User data or None

    Raises:
        HTTPException: If user not found
    """
    from packages.state.models.user import User
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user_row = result.scalar_one_or_none()

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_row


async def verify_user_password(
    password: str,
    user: Any,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify user password.

    Args:
        password: Provided password
        user: User data
        db: Database session

    Returns:
        User data

    Raises:
        HTTPException: If password is invalid
    """
    # Store password hash (would come from user model)
    stored_password = user.get("password")

    if not verify_password(password, stored_password):
        logger.warning(f"Invalid password for user {user.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    return user


async def check_rate_limit(
    request: Request,
    requests_per_period: int = settings.RATE_LIMIT_REQUESTS,
    period: int = settings.RATE_LIMIT_PERIOD,
    burst: int = settings.RATE_LIMIT_BURST,
) -> None:
    """
    Check rate limit for client.

    Args:
        request: Request object
        requests_per_period: Max requests per period
        period: Time period in seconds
        burst: Burst allowance

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get client IP
    client_ip = (
        request.client.host
        or request.headers.get("x-forwarded-for", request.client.host)
    )

    # Get or create rate limit key
    rate_limit_key = f"{client_ip}:{request.url.path}"

    # Check rate limit from Redis (simplified - would use Redis in production)
    # This is a placeholder for actual rate limiting implementation

    return None


async def get_active_user(
    user: Any = Depends(get_current_active_user),
    rate_limit: bool = settings.RATE_LIMIT_ENABLED,
) -> Any:
    """
    Get active user with optional rate limiting.

    Args:
        user: User from token
        rate_limit: Whether to check rate limits

    Returns:
        Active user data

    Raises:
        HTTPException: If rate limit exceeded
    """
    if rate_limit:
        await check_rate_limit(
            request=Request(),
            requests_per_period=100,
            period=60,
            burst=20,
        )

    return user
