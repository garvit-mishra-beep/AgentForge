"""
Authentication service.

Handles user authentication, token management, and RBAC.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.core.config import settings
from apps.api.core.database import async_session, engine
from apps.api.core.security import (
    oauth2_scheme,
    verify_token,
    hash_password,
    verify_password,
)
from apps.api.schemas.auth import UserCreate, UserResponse
from apps.api.dependencies.database import get_db
from packages.state.models.user import User

logger = logging.getLogger(__name__)


# ===============================
# USER REPOSITORY
# ===============================


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[dict]:
    """
    Get user by username.

    Args:
        db: Database session
        username: Username to lookup

    Returns:
        User data or None
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        logger.debug(f"User not found: {username}")
        return None

    user_dict = db_user.to_dict()
    user_dict["password"] = db_user.password_hash
    return user_dict


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[dict]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User data or None
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        logger.debug(f"User not found: {user_id}")
        return None

    user_dict = db_user.to_dict()
    user_dict["password"] = db_user.password_hash
    return user_dict


async def create_user(
    db: AsyncSession,
    user: UserCreate,
) -> UserResponse:
    """
    Create new user.

    Args:
        db: Database session
        user: User creation data

    Returns:
        Created user

    Raises:
        HTTPException: If user creation fails
    """
    # Check if username already exists
    existing = await get_user_by_username(db, user.username)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    # Hash password
    password_hash = hash_password(user.password)

    db_user = User(
        id=f"user-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=password_hash,
        is_active=True,
        is_superuser=False,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
    )


async def create_superuser(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> UserResponse:
    """
    Create superuser.

    Args:
        db: Database session
        username: Username
        email: Email
        password: Password

    Returns:
        Created superuser
    """
    password_hash = hash_password(password)

    db_user = User(
        id=f"user-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        username=username,
        email=email,
        full_name=f"Superuser ({username})",
        password_hash=password_hash,
        is_active=True,
        is_superuser=True,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
    )


async def get_user(
    db: AsyncSession,
    user_id: str,
) -> Optional[UserResponse]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User data or None
    """
    user_row = await get_user_by_id(db, user_id)

    if not user_row:
        return None

    return UserResponse(**user_row)


# ===============================
# TOKEN MANAGEMENT
# ===============================


async def create_access_token(
    subject: str,
    expires_delta: timedelta = None,
) -> str:
    """
    Create access token.

    Args:
        subject: Token subject
        expires_delta: Token expiration

    Returns:
        JWT access token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    token = verify_token(
        jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        ),
    )

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def create_refresh_token(
    subject: str,
    expires_delta: timedelta = None,
) -> str:
    """
    Create refresh token.

    Args:
        subject: Token subject
        expires_delta: Token expiration

    Returns:
        JWT refresh token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ===============================
# AUTH VALIDATION
# ===============================


async def validate_user_credentials(
    username: str,
    password: str,
    db: AsyncSession,
) -> Optional[dict]:
    """
    Validate user credentials.

    Args:
        username: Username
        password: Password
        db: Database session

    Returns:
        User data or None
    """
    # Get user by username
    user_row = await get_user_by_username(db, username)

    if not user_row:
        logger.warning(f"Invalid username or password for user {username}")
        return None

    # Verify password
    if not verify_password(password, user_row.get("password")):
        logger.warning(f"Invalid username or password for user {username}")
        return None

    return user_row
