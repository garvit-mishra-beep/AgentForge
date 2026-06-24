"""
JWT handler for AgentOS.

Handles JWT token generation and validation.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

# ===============================
# JWT CONTEXT
# ===============================


pwd_context = CryptContext(
    schemes=[settings.HASH_ALGORITHM],
    **{
        f"{settings.HASH_ALGORITHM}__rounds": settings.PBKDF2_ITERATIONS,
        f"{settings.HASH_ALGORITHM}__salt_size": settings.PBKDF2_SALT_LENGTH,
    }
)


# ===============================
# TOKEN GENERATION
# ===============================


def generate_access_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate JWT access token.

    Args:
        subject: Token subject (usually user ID)
        additional_claims: Additional claims to include

    Returns:
        JWT access token
    """
    # Calculate expiration
    exp_time = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    # Build payload
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": int(exp_time.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "access",
        "jti": str(time.time_ns()),
    }

    # Add additional claims
    if additional_claims:
        payload.update(additional_claims)

    try:
        # Encode token
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            headers={"alg": settings.JWT_ALGORITHM},
        )

        logger.debug(f"Access token generated for subject: {subject}")
        return token

    except Exception as e:
        logger.error(f"Failed to generate access token: {e}")
        raise


def generate_refresh_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate JWT refresh token.

    Args:
        subject: Token subject
        additional_claims: Additional claims

    Returns:
        JWT refresh token
    """
    # Calculate expiration
    exp_time = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    # Build payload
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": int(exp_time.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "refresh",
        "jti": str(time.time_ns()),
    }

    # Add additional claims
    if additional_claims:
        payload.update(additional_claims)

    try:
        # Encode token
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            headers={"alg": settings.JWT_ALGORITHM},
        )

        logger.debug(f"Refresh token generated for subject: {subject}")
        return token

    except Exception as e:
        logger.error(f"Failed to generate refresh token: {e}")
        raise


def generate_device_token(
    subject: str,
    device_id: str,
) -> str:
    """
    Generate device-specific token.

    Args:
        subject: Token subject
        device_id: Device identifier

    Returns:
        JWT device token
    """
    exp_time = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload: Dict[str, Any] = {
        "sub": subject,
        "device_id": device_id,
        "exp": int(exp_time.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "device",
    }

    try:
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token
    except Exception as e:
        logger.error(f"Failed to generate device token: {e}")
        raise


# ===============================
# TOKEN VALIDATION
# ===============================


def verify_token(
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Decoded token claims or None

    Raises:
        jwt.ExpiredSignatureError: If token expired
        jwt.InvalidTokenError: If token is invalid
    """
    if not token:
        logger.warning("Token verification failed: no token")
        return None

    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Check token type
        token_type = payload.get("type", "unknown")
        logger.info(
            "Token verified",
            token_type=token_type,
            subject=payload.get("sub"),
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: expired")
        return None

    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: {e}")
        return None

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def verify_access_token(
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Verify access token.

    Args:
        token: JWT access token

    Returns:
        Decoded token claims or None
    """
    return verify_token(token)


def verify_refresh_token(
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Verify refresh token.

    Args:
        token: JWT refresh token

    Returns:
        Decoded token claims or None
    """
    payload = verify_token(token)

    if payload:
        token_type = payload.get("type", "")

        if token_type != "refresh":
            logger.warning("Invalid refresh token: wrong token type")
            return None

    return payload


def verify_device_token(
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Verify device token.

    Args:
        token: JWT device token

    Returns:
        Decoded token claims or None
    """
    payload = verify_token(token)

    if payload:
        token_type = payload.get("type", "")

        if token_type != "device":
            logger.warning("Invalid device token: wrong token type")
            return None

    return payload


# ===============================
# TOKEN UTILITIES
# ===============================


def encode_token(
    payload: Dict[str, Any],
) -> str:
    """
    Encode payload to JWT token.

    Args:
        payload: Token payload

    Returns:
        Encoded JWT token
    """
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without verification.

    Args:
        token: JWT token

    Returns:
        Decoded payload or None
    """
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False},
        )
    except Exception:
        return None


def get_token_type(payload: Dict[str, Any]) -> str:
    """
    Get token type from payload.

    Args:
        payload: Token payload

    Returns:
        Token type string
    """
    return payload.get("type", "access")
