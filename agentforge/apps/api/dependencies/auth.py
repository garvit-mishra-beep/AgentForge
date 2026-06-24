from __future__ import annotations

import uuid
import hashlib
import logging
from typing import Optional

from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.security import verify_token, oauth2_scheme
from apps.api.core.database import get_db
from apps.api.core.exceptions import AuthenticationException
from apps.api.models import APIKey

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    token_value = token or (credentials.credentials if credentials else None)

    if not token_value:
        raise AuthenticationException("No authentication credentials provided")

    payload = verify_token(token_value)
    if payload:
        return {
            "sub": payload.get("sub", ""),
            "tenant_id": payload.get("tenant_id", ""),
            "type": "jwt",
        }

    result = await db.execute(select(APIKey).where(APIKey.key_hash == hashlib.sha256(token_value.encode()).hexdigest()))
    api_key = result.scalar_one_or_none()
    if api_key:
        if api_key.expires_at and api_key.expires_at < func.now():
            raise AuthenticationException("API key has expired")
        api_key.last_used_at = func.now()
        await db.flush()
        return {
            "sub": str(api_key.tenant_id),
            "tenant_id": str(api_key.tenant_id),
            "type": "api_key",
            "permissions": api_key.permissions,
        }

    raise AuthenticationException("Invalid or expired token")


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user:
        raise AuthenticationException("Not authenticated")
    return current_user


def get_tenant_id(user: dict = Depends(get_current_active_user)) -> uuid.UUID:
    return uuid.UUID(user.get("tenant_id", "00000000-0000-0000-0000-000000000000"))
