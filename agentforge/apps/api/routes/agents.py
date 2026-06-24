from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.schemas import AgentCreate, AgentUpdate, AgentResponse, InvokeResponse
from apps.api.services import AgentService, ExecutionService
from apps.api.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    data: AgentCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = AgentService(db)
    return await service.create(tenant_id, data)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = AgentService(db)
    return await service.list(tenant_id, skip, limit, status)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = AgentService(db)
    agent = await service.get(agent_id, tenant_id=tenant_id)
    if not agent:
        raise NotFoundException("Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = AgentService(db)
    agent = await service.update(agent_id, data, tenant_id=tenant_id)
    if not agent:
        raise NotFoundException("Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    service = AgentService(db)
    deleted = await service.delete(agent_id, tenant_id=tenant_id)
    if not deleted:
        raise NotFoundException("Agent not found")


@router.post("/{agent_id}/invoke", response_model=InvokeResponse)
async def invoke_agent(
    agent_id: uuid.UUID,
    input_data: dict,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_active_user),
):
    agent_service = AgentService(db)
    exec_service = ExecutionService(db)

    agent = await agent_service.get(agent_id, tenant_id=tenant_id)
    if not agent:
        raise NotFoundException("Agent not found")

    execution = await exec_service.create(tenant_id, agent_id, input_data)
    await exec_service.update_status(execution.id, "running")

    import time
    start = time.time()

    try:
        from packages.llm.src import get_llm
        from apps.api.core.config import settings
        llm = get_llm(
            provider=agent.llm_config.get("provider", "openai"),
            model=agent.llm_config.get("model", "gpt-4o"),
            api_key=settings.OPENAI_API_KEY,
        )
        messages = [{"role": "system", "content": agent.system_prompt or "You are a helpful AI assistant."}]
        messages.append({"role": "user", "content": str(input_data.get("message", input_data))})

        response = await llm.generate(messages, temperature=agent.llm_config.get("temperature", 0.7))
        duration = int((time.time() - start) * 1000)
        tokens_in = response.get("tokens_in", 0)
        tokens_out = response.get("tokens_out", 0)
        cost = (tokens_in * 0.000003) + (tokens_out * 0.000015)

        steps = [{
            "node": "llm_call",
            "llm_calls": 1,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_ms": duration,
            "tool_calls": [],
        }]

        await exec_service.update_result(execution.id, {"response": response.get("content", "")}, tokens_in + tokens_out, cost, duration, steps)
        await exec_service.update_status(execution.id, "completed")

        return InvokeResponse(
            execution_id=execution.id,
            status="completed",
            output=response.get("content", ""),
            tokens_used=tokens_in + tokens_out,
            duration_ms=duration,
        )
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        await exec_service.update_status(execution.id, "failed", error=str(e))
        logger.exception(f"Agent invocation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
