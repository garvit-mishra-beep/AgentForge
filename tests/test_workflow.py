import pytest
import time
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from packages.orchestration.workflows.software_development_workflow import create_workflow
from apps.api.core.config import settings

@pytest.mark.asyncio
async def test_postgres_checkpointer_integration():
    from apps.api.core.database import init_db
    await init_db()

    # Setup standard PostgreSQL connection pool (remove asyncpg prefix)
    conninfo = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    async with AsyncConnectionPool(conninfo=conninfo, min_size=1, max_size=2, kwargs={"autocommit": True}) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        
        # Compile graph
        graph = create_workflow(checkpointer=checkpointer)
        
        # Make a fast mock execution
        execution_id = f"test-exec-{int(time.time())}"
        config = {"configurable": {"thread_id": execution_id}}

        # Create parent Workflow and Execution records in DB to satisfy foreign key constraints
        from packages.state.models.workflow import Workflow, Execution
        from apps.api.core.database import async_session
        from sqlalchemy import select
        async with async_session() as session:
            wf_res = await session.execute(select(Workflow).where(Workflow.workflow_id == "test-wf"))
            wf = wf_res.scalar_one_or_none()
            if not wf:
                wf = Workflow(
                    workflow_id="test-wf",
                    name="Test Workflow",
                    description="Workflow for unit testing",
                    status="created",
                    inputs="{}",
                    output_schema="{}"
                )
                session.add(wf)
                await session.flush() # Force insert Workflow first
            
            exec_record = Execution(
                execution_id=execution_id,
                workflow_id="test-wf",
                status="pending",
                priority=5,
                cancel_on_timeout=True,
                result="{}",
                checkpoint="{}"
            )
            session.add(exec_record)
            await session.commit()
        
        initial_state = {
            "workflow_id": "test-wf",
            "execution_id": execution_id,
            "created_at": time.time(),
            "task_description": "Build a sample service with test_fail prompt to trigger fix loop",
            "requirements": [
                {"name": "Step 1", "description": "Mock phase 1", "effort": "1h"}
            ],
            "plan": None,
            "tasks": [],
            "implementation_status": None,
            "code_artifacts": [],
            "implementation_logs": [],
            "review_result": None,
            "review_comments": [],
            "similar_projects": [],
            "retry_count": 0,
            "max_retries": 3,
            "escalation_threshold": 3,
            "escalation_reason": None,
            "escalation_history": []
        }
        
        # Invoke LangGraph async
        result = await graph.ainvoke(initial_state, config=config)
        
        # Verify execution completed and checkpoint saved
        assert result is not None
        assert "plan" in result
        assert len(result["code_artifacts"]) > 0
        assert result["retry_count"] >= 1  # Verify Coder fix loop ran
        
        # Fetch checkpoint to assert it was saved in PostgreSQL
        checkpoint = await checkpointer.aget(config)
        assert checkpoint is not None
        assert checkpoint["channel_values"]["retry_count"] == result["retry_count"]
