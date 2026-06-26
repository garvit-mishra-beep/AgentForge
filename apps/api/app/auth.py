"""JWT authentication and authorization middleware with refresh token support."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from core.config import settings

logger = logging.getLogger(__name__)

AUTH_COOKIE_NAME = "agentforge_token"
REFRESH_COOKIE_NAME = "agentforge_refresh"
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

_OPEN_ROUTES = {
    "GET:/api/v1/health",
    "POST:/api/v1/auth/login",
    "POST:/api/v1/auth/register",
    "POST:/api/v1/auth/refresh",
    "GET:/api/v1/keys/providers",
    "POST:/api/v1/keys/validate",
    "GET:/docs",
    "GET:/openapi.json",
    "GET:/redoc",
}


def _get_jwt_secret() -> str:
    return settings.jwt_secret or "dev-secret-do-not-use-in-production"


def _get_refresh_secret() -> str:
    return settings.jwt_refresh_secret or _get_jwt_secret()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def create_token(user_id: str) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "type": "access",
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "access":
            return None
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_refresh_token(user_id: str) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_expire_days),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _get_refresh_secret(), algorithm="HS256")


def verify_refresh_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            _get_refresh_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "type"]},
        )
        if payload.get("type") != "refresh":
            return None
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(request: Request) -> str | None:
    if not settings.auth_enabled:
        return DEMO_USER_ID

    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return None

    return verify_token(token)


async def require_user(request: Request) -> str:
    user_id = await get_current_user(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


async def auth_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method
    route_key = f"{method}:{path}"

    for prefix in ("/api/v1/", "/docs", "/openapi.json", "/redoc"):
        if path.startswith(prefix):
            break
    else:
        return await call_next(request)

    if route_key in _OPEN_ROUTES or any(
        path.startswith(p) for p in ("/docs", "/openapi.json", "/redoc")
    ):
        return await call_next(request)

    user_id = await get_current_user(request)
    if user_id is None and settings.auth_enabled:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"},
        )

    request.state.user_id = user_id or DEMO_USER_ID
    return await call_next(request)
