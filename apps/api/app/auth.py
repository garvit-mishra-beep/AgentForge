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
    # GitHub webhooks authenticate via HMAC signature, not a user JWT.
    "POST:/api/v1/integrations/github/webhook",
    "GET:/api/v1/integrations/github/status",
    "GET:/docs",
    "GET:/openapi.json",
    "GET:/redoc",
}


def _get_jwt_secret() -> str:
    return settings.jwt_secret or "dev-secret-do-not-use-in-production"


def _get_refresh_secret() -> str:
    # A distinct refresh secret is required when auth is on (enforced by
    # settings.validate()). The access-secret fallback only applies in the
    # auth-disabled local/demo mode (TOP_FINDINGS #7).
    if settings.jwt_refresh_secret:
        return settings.jwt_refresh_secret
    return _get_jwt_secret()


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


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Mint a refresh token. Returns ``(token, jti, expires_at)``.

    The caller is expected to persist ``jti``/``expires_at`` via
    :func:`store_refresh_token` so the token can later be rotated or revoked.
    """
    now = datetime.now(tz=UTC)
    expires_at = now + timedelta(days=settings.jwt_refresh_expire_days)
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expires_at,
        "type": "refresh",
        "jti": jti,
    }
    token = jwt.encode(payload, _get_refresh_secret(), algorithm="HS256")
    return token, jti, expires_at


def decode_refresh_token(token: str) -> dict | None:
    """Validate signature/expiry/type and return the full payload (incl. jti)."""
    try:
        payload = jwt.decode(
            token,
            _get_refresh_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "type", "jti"]},
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> str | None:
    """Backwards-compatible helper: return the subject (user id) or ``None``."""
    payload = decode_refresh_token(token)
    return payload["sub"] if payload else None


# â”€â”€ Refresh-token persistence (rotation + revocation) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


async def store_refresh_token(db, jti: str, user_id: str, expires_at: datetime) -> None:
    await db.execute(
        "INSERT INTO refresh_tokens (jti, user_id, expires_at) VALUES ($1, $2, $3)",
        jti, user_id, expires_at,
    )


async def refresh_token_active(db, jti: str, user_id: str) -> bool:
    """True only if the jti is stored, unrevoked, unexpired and owned by user."""
    return bool(
        await db.fetchval(
            """
            SELECT 1 FROM refresh_tokens
            WHERE jti = $1 AND user_id = $2
              AND revoked = FALSE AND expires_at > NOW()
            """,
            jti, user_id,
        )
    )


async def revoke_refresh_token(db, jti: str, replaced_by: str | None = None) -> bool:
    """Revoke a single refresh token. Returns True if a row was updated."""
    result = await db.execute(
        "UPDATE refresh_tokens SET revoked = TRUE, replaced_by = $2 WHERE jti = $1 AND revoked = FALSE",
        jti, replaced_by,
    )
    # asyncpg returns a status string like "UPDATE 1".
    return result.endswith("1")


async def revoke_all_refresh_tokens(db, user_id: str) -> None:
    await db.execute(
        "UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = $1 AND revoked = FALSE",
        user_id,
    )


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


async def validate_websocket_token(token: str) -> str | None:
    """Validate a JWT token for WebSocket connections.
    Returns user_id if valid, None otherwise.
    """
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
