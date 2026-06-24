from __future__ import annotations

import uuid
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.security import create_access_token, create_refresh_token, verify_token, verify_password, hash_password
from apps.api.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


@router.post("/token")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    tenant_id = str(user.tenant_id)
    extra = {"tenant_id": tenant_id}
    access_token = create_access_token(subject=user.username, tenant_id=tenant_id, extra_claims=extra)
    refresh_token = create_refresh_token(subject=user.username, tenant_id=tenant_id, extra_claims=extra)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    subject = payload.get("sub", "")
    tenant_id = payload.get("tenant_id", "")

    result = await db.execute(select(User).where(User.username == subject))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    extra = {"tenant_id": tenant_id}
    access_token = create_access_token(subject=subject, tenant_id=tenant_id, extra_claims=extra)
    new_refresh = create_refresh_token(subject=subject, tenant_id=tenant_id, extra_claims=extra)
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    tenant_id = uuid.uuid4()
    user = User(
        tenant_id=tenant_id,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    extra = {"tenant_id": str(tenant_id)}
    access_token = create_access_token(subject=user.username, tenant_id=str(tenant_id), extra_claims=extra)
    refresh_token = create_refresh_token(subject=user.username, tenant_id=str(tenant_id), extra_claims=extra)
    return {
        "user_id": str(user.id),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}
