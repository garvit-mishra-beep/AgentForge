"""Authentication routes - login, register, refresh."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import (
    create_refresh_token,
    create_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from core.config import settings
from core.observability import emit
from core.redis import failed_login_attempt, is_login_locked, reset_login_attempts
from models.schemas import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    token: str
    refresh_token: str


def _db(request: Request):
    return request.app.state.db


def _bf_identifier(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{email}:{client_ip}"


@router.post("/login")
async def login(body: LoginRequest, request: Request) -> AuthResponse:
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
    refresh_token = create_refresh_token(user_id)

    return AuthResponse(
        token=token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=row["email"],
        name=row["name"],
    )


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, request: Request) -> AuthResponse:
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
    refresh_token = create_refresh_token(user_id)

    return AuthResponse(
        token=token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=body.email,
        name=body.name,
    )


@router.post("/refresh")
async def refresh(body: RefreshRequest) -> RefreshResponse:
    user_id = verify_refresh_token(body.refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_token = create_token(user_id)
    new_refresh = create_refresh_token(user_id)

    return RefreshResponse(token=new_token, refresh_token=new_refresh)
