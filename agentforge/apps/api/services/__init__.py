from __future__ import annotations

import uuid
import time
import logging
from typing import Any, List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models import Agent, Workflow, Execution, APIKey
from apps.api.schemas import AgentCreate, AgentUpdate, WorkflowCreate, WorkflowUpdate

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            llm_config=data.llm_config,
            system_prompt=data.system_prompt,
            tools=data.tools,
            memory_config=data.memory_config,
        )
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def get(self, agent_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None) -> Optional[Agent]:
        query = select(Agent).where(Agent.id == agent_id)
        if tenant_id:
            query = query.where(Agent.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, tenant_id: uuid.UUID, slug: str) -> Optional[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.tenant_id == tenant_id, Agent.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List[Agent]:
        query = select(Agent).where(Agent.tenant_id == tenant_id)
        if status:
            query = query.where(Agent.status == status)
        query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, agent_id: uuid.UUID, data: AgentUpdate, tenant_id: Optional[uuid.UUID] = None) -> Optional[Agent]:
        agent = await self.get(agent_id, tenant_id=tenant_id)
        if not agent:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(agent, key, value)
        agent.version += 1
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def delete(self, agent_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None) -> bool:
        agent = await self.get(agent_id, tenant_id=tenant_id)
        if not agent:
            return False
        await self.db.delete(agent)
        await self.db.flush()
        return True


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: uuid.UUID, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            definition=data.definition,
        )
        self.db.add(workflow)
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def get(self, workflow_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None) -> Optional[Workflow]:
        query = select(Workflow).where(Workflow.id == workflow_id)
        if tenant_id:
            query = query.where(Workflow.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Workflow]:
        query = select(Workflow).where(Workflow.tenant_id == tenant_id).offset(skip).limit(limit).order_by(Workflow.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, workflow_id: uuid.UUID, data: WorkflowUpdate, tenant_id: Optional[uuid.UUID] = None) -> Optional[Workflow]:
        workflow = await self.get(workflow_id, tenant_id=tenant_id)
        if not workflow:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(workflow, key, value)
        workflow.version += 1
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def delete(self, workflow_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None) -> bool:
        workflow = await self.get(workflow_id, tenant_id=tenant_id)
        if not workflow:
            return False
        await self.db.delete(workflow)
        await self.db.flush()
        return True


class ExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: uuid.UUID, agent_id: Optional[uuid.UUID], input_data: dict) -> Execution:
        execution = Execution(
            tenant_id=tenant_id,
            agent_id=agent_id,
            input=input_data,
            status="pending",
        )
        self.db.add(execution)
        await self.db.flush()
        await self.db.refresh(execution)
        return execution

    async def get(self, execution_id: uuid.UUID, tenant_id: Optional[uuid.UUID] = None) -> Optional[Execution]:
        query = select(Execution).where(Execution.id == execution_id)
        if tenant_id:
            query = query.where(Execution.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 50,
        agent_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> List[Execution]:
        query = select(Execution).where(Execution.tenant_id == tenant_id)
        if agent_id:
            query = query.where(Execution.agent_id == agent_id)
        if status:
            query = query.where(Execution.status == status)
        query = query.offset(skip).limit(limit).order_by(Execution.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(self, execution_id: uuid.UUID, status: str, error: Optional[str] = None) -> Optional[Execution]:
        execution = await self.get(execution_id)
        if not execution:
            return None
        execution.status = status
        if error:
            execution.error = error
        if status in ("completed", "failed", "cancelled"):
            execution.completed_at = func.now()
        await self.db.flush()
        await self.db.refresh(execution)
        return execution

    async def update_result(self, execution_id: uuid.UUID, output: dict, tokens: int, cost: float, duration_ms: int, steps: list) -> Optional[Execution]:
        execution = await self.get(execution_id)
        if not execution:
            return None
        execution.output = output
        execution.total_tokens = tokens
        execution.total_cost_usd = cost
        execution.duration_ms = duration_ms
        execution.steps = steps
        await self.db.flush()
        await self.db.refresh(execution)
        return execution

    async def get_metrics(self, tenant_id: uuid.UUID, agent_id: Optional[uuid.UUID] = None, days: int = 7):
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(
            func.count(Execution.id),
            func.sum(Execution.total_tokens),
            func.sum(Execution.total_cost_usd),
            func.avg(Execution.duration_ms),
        ).where(
            Execution.tenant_id == tenant_id,
            Execution.created_at >= since,
        )
        if agent_id:
            query = query.where(Execution.agent_id == agent_id)
        result = await self.db.execute(query)
        row = result.one()
        return {
            "total_executions": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost_usd": float(row[2] or 0.0),
            "avg_duration_ms": float(row[3] or 0.0),
        }
