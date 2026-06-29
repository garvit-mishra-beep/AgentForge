"""Authentication routes - login, register, refresh, logout, Google OAuth."""

import secrets
import logging
import uuid
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.auth import (
    create_refresh_token,
    create_token,
    decode_refresh_token,
    hash_password,
    refresh_token_active,
    require_user,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    store_refresh_token,
    verify_password,
    set_auth_cookies,
    clear_auth_cookies,
    AUTH_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
)
from core.config import settings
from core.observability import emit
from core.redis import failed_login_attempt, is_login_locked, reset_login_attempts
from models.schemas import AuthResponse, LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    token: str
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


router = APIRouter(prefix="/auth", tags=["auth"])


def _db(request: Request):
    return request.app.state.db


def _bf_identifier(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{email}:{client_ip}"


@router.post("/login")
async def login(body: LoginRequest, request: Request, response: Response) -> AuthResponse:
    db = _db(request)
    bf_id = _bf_identifier(request, body.email)

    if await is_login_locked(bf_id, settings.brute_force_max_attempts, settings.brute_force_lockout_seconds):
        emit("brute_force_lockout", {"email": body.email, "bf_id": bf_id})
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )

    row = await db.fetchrow(
        "SELECT id, email, name, password_hash FROM users WHERE email = $1",
        body.email,
    )
    if not row:
        attempts = await failed_login_attempt(bf_id, settings.brute_force_lockout_seconds)
        emit("auth_failed", {"email": body.email, "reason": "user_not_found", "attempts": attempts})
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(body.password, row["password_hash"]):
        attempts = await failed_login_attempt(bf_id, settings.brute_force_lockout_seconds)
        emit("auth_failed", {"email": body.email, "reason": "wrong_password", "attempts": attempts})
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await reset_login_attempts(bf_id)

    user_id = str(row["id"])
    token = create_token(user_id)
    refresh_token, jti, expires_at = create_refresh_token(user_id)
    await store_refresh_token(db, jti, user_id, expires_at)

    set_auth_cookies(response, token, refresh_token)

    return AuthResponse(
        token=token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=row["email"],
        name=row["name"],
    )


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, request: Request, response: Response) -> AuthResponse:
    db = _db(request)

    existing = await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        body.email,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(body.password)

    await db.execute(
        "INSERT INTO users (id, email, name, password_hash) VALUES ($1, $2, $3, $4)",
        user_id, body.email, body.name, pw_hash,
    )

    token = create_token(user_id)
    refresh_token, jti, expires_at = create_refresh_token(user_id)
    await store_refresh_token(db, jti, user_id, expires_at)

    set_auth_cookies(response, token, refresh_token)

    return AuthResponse(
        token=token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=body.email,
        name=body.name,
    )


@router.post("/refresh")
async def refresh(request: Request, response: Response, body: RefreshRequest | None = None) -> RefreshResponse:
    """Rotate a refresh token: validate, revoke the old jti, issue a new pair.

    Reuse of an already-rotated/revoked token is rejected (401) — this both
    enforces single-use rotation and detects token theft.
    """
    db = _db(request)
    refresh_token = None
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    else:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload["sub"]
    old_jti = payload["jti"]

    if not await refresh_token_active(db, old_jti, user_id):
        # Token was never issued by us, already used, revoked, or expired.
        emit("refresh_token_reuse", {"user_id": user_id, "jti": old_jti})
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_token = create_token(user_id)
    new_refresh, new_jti, expires_at = create_refresh_token(user_id)
    await store_refresh_token(db, new_jti, user_id, expires_at)
    await revoke_refresh_token(db, old_jti, replaced_by=new_jti)

    set_auth_cookies(response, new_token, new_refresh)

    return RefreshResponse(token=new_token, refresh_token=new_refresh)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, body: LogoutRequest | None = None, user_id: str = Depends(require_user)):
    """Revoke the presented refresh token and clear cookies. Idempotent."""
    db = _db(request)
    refresh_token = None
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    else:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if refresh_token:
        payload = decode_refresh_token(refresh_token)
        if payload and payload.get("sub") == user_id:
            await revoke_refresh_token(db, payload["jti"])

    clear_auth_cookies(response)
    return None


@router.post("/logout-all", status_code=204)
async def logout_all(request: Request, response: Response, user_id: str = Depends(require_user)):
    """Revoke every refresh token for the current user and clear cookies."""
    db = _db(request)
    await revoke_all_refresh_tokens(db, user_id)
    clear_auth_cookies(response)
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, user_id: str = Depends(require_user)) -> UserResponse:
    """Return user details for active session."""
    db = _db(request)
    row = await db.fetchrow(
        "SELECT id, email, name FROM users WHERE id = $1",
        user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        name=row["name"],
    )


@router.get("/google")
async def google_login(request: Request):
    state = secrets.token_urlsafe(32)
    redirect_uri = f"{request.base_url.scheme}://{request.base_url.netloc}/api/v1/auth/google/callback"
    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
    )

    response = RedirectResponse(url=google_url)
    response.set_cookie(
        key="google_oauth_state",
        value=state,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=600,
        path="/",
    )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, response: Response, code: str | None = None, state: str | None = None):
    db = _db(request)
    cookie_state = request.cookies.get("google_oauth_state")
    if not cookie_state or not state or cookie_state != state:
        raise HTTPException(status_code=400, detail="OAuth state verification failed")

    # Set 302 redirect response
    redirect_resp = RedirectResponse(url=f"{settings.frontend_url}/dashboard")
    redirect_resp.delete_cookie(key="google_oauth_state", path="/")

    if not code:
        raise HTTPException(status_code=400, detail="OAuth code missing")

    redirect_uri = f"{request.base_url.scheme}://{request.base_url.netloc}/api/v1/auth/google/callback"

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        )
        if not token_res.is_success:
            logger.error("Failed to exchange code: %s", token_res.text)
            raise HTTPException(status_code=400, detail="Failed to exchange Google OAuth code")

        token_data = token_res.json()
        access_token = token_data.get("access_token")

        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if not userinfo_res.is_success:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user profile")

        user_info = userinfo_res.json()
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0] if email else "User")

    if not email:
        raise HTTPException(status_code=400, detail="Google user profile has no email")

    row = await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        email,
    )
    if row:
        user_id = str(row["id"])
    else:
        user_id = str(uuid.uuid4())
        pw_hash = hash_password(secrets.token_urlsafe(16))
        await db.execute(
            "INSERT INTO users (id, email, name, password_hash) VALUES ($1, $2, $3, $4)",
            user_id, email, name, pw_hash,
        )

    token = create_token(user_id)
    refresh_token, jti, expires_at = create_refresh_token(user_id)
    await store_refresh_token(db, jti, user_id, expires_at)

    set_auth_cookies(redirect_resp, token, refresh_token)
    return redirect_resp
