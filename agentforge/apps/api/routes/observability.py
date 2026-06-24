from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.services import ExecutionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/usage")
async def get_usage(
    days: int = Query(7, ge=1, le=90),
    agent_id: Optional[uuid.UUID] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = ExecutionService(db)
    return await service.get_metrics(tenant_id, agent_id, days)
