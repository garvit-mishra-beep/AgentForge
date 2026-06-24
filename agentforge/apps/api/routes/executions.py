from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.schemas import ExecutionResponse
from apps.api.services import ExecutionService
from apps.api.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("", response_model=list[ExecutionResponse])
async def list_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    agent_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = ExecutionService(db)
    return await service.list(tenant_id, skip, limit, agent_id, status)


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = ExecutionService(db)
    execution = await service.get(execution_id, tenant_id=tenant_id)
    if not execution:
        raise NotFoundException("Execution not found")
    return execution
