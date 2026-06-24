from __future__ import annotations

import uuid
import logging
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi.security import OAuth2PasswordBearer

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

JWT_ISSUER = "agentforge-api"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_jti() -> str:
    return uuid.uuid4().hex


def create_access_token(
    subject: str,
    tenant_id: str = "",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = _now() + expires_delta
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": _now(),
        "iss": JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": _make_jti(),
        "type": "access",
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    tenant_id: str = "",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = _now() + expires_delta
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": _now(),
        "iss": JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": _make_jti(),
        "type": "refresh",
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            leeway=10,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidAudienceError:
        logger.warning("Token has invalid audience")
        return None
    except jwt.InvalidIssuerError:
        logger.warning("Token has invalid issuer")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
