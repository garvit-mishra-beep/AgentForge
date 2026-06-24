"""
Authentication and security utilities.

JWT, OAuth2, password hashing with production-grade implementations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

# ===============================
# SECURITY CONFIGURATION
# ===============================

# OAuth2 password bearer for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    description="JWT access token"
)

# Password hashing context using Passlib
pwd_context = CryptContext(schemes=[settings.HASH_ALGORITHM])

# ===============================
# JWT ENCODING/DECODING
# ===============================


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict | None = None
) -> str:
    """
    Create JWT access token.

    Args:
        subject: Token payload subject (typically user ID)
        expires_delta: Optional expiration override
        additional_claims: Additional claims to include

    Returns:
        str: Encoded JWT token

    Raises:
        Exception: If token creation fails
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    if additional_claims:
        payload.update(additional_claims)

    try:
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.debug(f"Access token created for subject: {subject}")
        return token
    except jwt.PyJWTError as e:
        logger.error(f"Failed to create JWT token: {e}")
        raise


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None
) -> str:
    """
    Create JWT refresh token.

    Args:
        subject: Token payload subject
        expires_delta: Token expiration

    Returns:
        str: Encoded refresh token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    try:
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token
    except jwt.PyJWTError as e:
        logger.error(f"Failed to create refresh token: {e}")
        raise


def verify_token(token: str) -> dict | None:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token to verify

    Returns:
        dict: Decoded token claims or None if invalid

    Raises:
        Exception: If token verification fails
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def hash_password(plain_password: str) -> str:
    """
    Hash password using passlib.

    Args:
        plain_password: Plain text password

    Returns:
        str: Hashed password

    Raises:
        Exception: If hashing fails
    """
    try:
        hashed = pwd_context.hash(plain_password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password
        hashed_password: Stored password hash

    Returns:
        bool: True if passwords match
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Alias for hash_password for consistency.

    Args:
        password: Password to hash

    Returns:
        str: Hashed password
    """
    return hash_password(password)


# ===============================
# AUTH DEPENDENCY
# ===============================


async def get_current_user(token: str | None = None) -> dict | None:
    """
    Get current authenticated user from token.

    Args:
        token: JWT token (optional - can be from request)

    Returns:
        dict: User data or None if unauthenticated

    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    subject = payload.get("sub")
    if not subject:
        return None

    return {"sub": subject, "payload": payload}


async def get_current_active_user(
    token: str | None = None
) -> dict | None:
    """
    Get current active (not expired) user.

    Args:
        token: JWT token

    Returns:
        dict: Active user data or None

    Raises:
        HTTPException: If token expired or invalid
    """
    user = await get_current_user(token)
    if not user:
        return None

    # Check for expired token claims
    if "exp" in user.get("payload", {}):
        if datetime.utcnow() > datetime.fromtimestamp(user["payload"]["exp"]):
            logger.warning("Token expired")
            return None

    return user
