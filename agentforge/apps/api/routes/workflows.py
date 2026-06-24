from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from apps.api.services import WorkflowService
from apps.api.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = WorkflowService(db)
    return await service.create(tenant_id, data)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = WorkflowService(db)
    return await service.list(tenant_id, skip, limit)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = WorkflowService(db)
    workflow = await service.get(workflow_id, tenant_id=tenant_id)
    if not workflow:
        raise NotFoundException("Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = WorkflowService(db)
    workflow = await service.update(workflow_id, data, tenant_id=tenant_id)
    if not workflow:
        raise NotFoundException("Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = WorkflowService(db)
    deleted = await service.delete(workflow_id, tenant_id=tenant_id)
    if not deleted:
        raise NotFoundException("Workflow not found")
