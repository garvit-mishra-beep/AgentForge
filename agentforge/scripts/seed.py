from __future__ import annotations

import asyncio
import uuid

from apps.api.core.database import init_db, async_session
from apps.api.services import AgentService, WorkflowService
from apps.api.schemas import AgentCreate, WorkflowCreate


async def seed():
    await init_db()
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    async with async_session() as db:
        agent_svc = AgentService(db)
        wf_svc = WorkflowService(db)

        agent = await agent_svc.create(tenant_id, AgentCreate(
            name="Assistant",
            slug="assistant",
            description="General purpose AI assistant with web search",
            llm_config={"provider": "openai", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 4096},
            system_prompt="You are a helpful AI assistant. Answer questions accurately and concisely.",
            tools=["web_search", "calculator", "current_datetime"],
            memory_config={"type": "short_term", "turns": 20},
        ))
        print(f"Created agent: {agent.name} ({agent.id})")

        agent2 = await agent_svc.create(tenant_id, AgentCreate(
            name="Code Reviewer",
            slug="code-reviewer",
            description="Reviews code for quality and security issues",
            llm_config={"provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "temperature": 0.3, "max_tokens": 8192},
            system_prompt="You are a senior code reviewer. Analyze code for bugs, security issues, and best practices.",
            tools=[],
            memory_config={"type": "short_term", "turns": 10},
        ))
        print(f"Created agent: {agent2.name} ({agent2.id})")

        wf = await wf_svc.create(tenant_id, WorkflowCreate(
            name="Research & Summarize",
            description="Search the web and summarize findings",
            definition={
                "nodes": [
                    {"id": "search", "type": "agent", "agent_id": str(agent.id), "label": "Search Agent"},
                    {"id": "output", "type": "output", "label": "Final Output"},
                ],
                "edges": [
                    {"from": "search", "to": "output"},
                ],
            },
        ))
        print(f"Created workflow: {wf.name} ({wf.id})")

    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
