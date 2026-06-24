"""
Workflow management routes.

CRUD operations for workflow execution and monitoring backed by PostgreSQL.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies.auth import get_current_active_user
from apps.api.dependencies.database import get_db
from apps.api.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStatus,
    ExecutionCreate,
    ExecutionResponse,
    WorkflowExecution,
)
from apps.api.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse,
)
from apps.api.services.workflow_service import (
    create_workflow_service,
    create_execution_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ===============================
# BACKGROUND WORKFLOW EXECUTION
# ===============================

async def run_langgraph_workflow_background(
    workflow_id: str,
    execution_id: str,
    task_description: str,
    inputs: dict
):
    """
    Executes the LangGraph Software Development Workflow in a background task.
    Updates database status and broadcasts real-time steps via WebSockets.
    """
    from packages.orchestration.workflows.software_development_workflow import create_workflow
    from apps.api.core.database import async_session
    from apps.api.services.workflow_service import create_execution_service
    from apps.api.websocket.manager import get_manager
    from apps.api.core.config import settings
    from psycopg_pool import AsyncConnectionPool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    logger.info(f"Starting background workflow execution: {execution_id}")

    # Build initial state
    initial_state = {
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "created_at": time.time(),
        "task_description": task_description,
        "requirements": inputs.get("requirements", [
            {"name": "Architecture & Schema Setup", "description": f"Design and implement database schema for: {task_description[:50]}", "effort": "2h"},
            {"name": "Core Logical Implementation", "description": "Write business logic and endpoints", "effort": "4h"},
            {"name": "Unit Tests & Edge Cases", "description": "Write unit tests for the core logic", "effort": "2h"}
        ]),
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

    conninfo = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    try:
        async with AsyncConnectionPool(conninfo=conninfo, min_size=1, max_size=2, kwargs={"autocommit": True}) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()

            # Compile graph with checkpointer
            graph = create_workflow(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": execution_id}}

            # Invoke LangGraph async
            result = await graph.ainvoke(initial_state, config=config)

        # Complete execution in DB
        async with async_session() as session:
            exec_service = create_execution_service(session)
            await exec_service.update_execution_status(execution_id, "completed")
            await exec_service.update_execution_result(execution_id, result, result)
            
            # Write files to disk under projects/{execution_id}
            exec_service.write_project_files_to_disk(execution_id, result.get("code_artifacts", []))
            
            await exec_service.add_event(execution_id, "execution.completed", {
                "workflow_id": workflow_id,
                "status": "completed",
                "message": "Workflow execution completed successfully!"
            })

        # Broadcast completed status
        manager = get_manager()
        await manager.broadcast(workflow_id, {
            "type": "execution.completed",
            "payload": {
                "workflowId": workflow_id,
                "executionId": execution_id,
                "status": "completed"
            }
        })

    except Exception as e:
        logger.error(f"Error running background workflow {execution_id}: {e}", exc_info=True)
        async with async_session() as session:
            exec_service = create_execution_service(session)
            await exec_service.update_execution_status(execution_id, "failed", error=str(e))
            await exec_service.add_event(execution_id, "execution.failed", {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "message": f"Execution failed: {str(e)}"
            })

        # Broadcast failed status
        manager = get_manager()
        await manager.broadcast(workflow_id, {
            "type": "execution.failed",
            "payload": {
                "workflowId": workflow_id,
                "executionId": execution_id,
                "error": str(e)
            }
        })


# ===============================
# WORKFLOW ROUTES
# ===============================


@router.post(
    "/workflows",
    tags=["Workflows"],
    summary="Create workflow",
    description="Create a new workflow definition",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    workflow: WorkflowCreate,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new workflow definition and persist to DB.
    """
    workflow_service = create_workflow_service(db)
    creator_id = user.get("sub") if isinstance(user, dict) else getattr(user, "id", None)
    return await workflow_service.create(workflow, creator_id=creator_id)


@router.get(
    "/workflows",
    tags=["Workflows"],
    summary="List workflows",
    description="List all workflows",
    response_model=List[WorkflowResponse],
)
async def list_workflows(
    offset: int = Query(0, ge=0, le=10000),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[WorkflowStatus] = None,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[Any]:
    """
    List workflows.
    """
    workflow_service = create_workflow_service(db)
    return await workflow_service.list_workflows(offset, limit, status)


# ===============================
# MEMORY ROUTES
# ===============================


@router.post(
    "/workflows/memories",
    tags=["Memories"],
    summary="Create project memory",
    description="Manually insert a project memory plan & architecture",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    memory: MemoryCreate,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workflow_service = create_workflow_service(db)
    try:
        new_memory = await workflow_service.create_memory(
            project_key=memory.project_key,
            description=memory.description,
            architecture=memory.architecture,
            code_artifacts=memory.code_artifacts,
        )
        return workflow_service._to_memory_response(new_memory)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/workflows/memories",
    tags=["Memories"],
    summary="List project memories",
    description="Retrieve a paginated list of project memories",
    response_model=List[MemoryResponse],
)
async def list_memories(
    offset: int = Query(0, ge=0, le=10000),
    limit: int = Query(20, ge=1, le=100),
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[Any]:
    workflow_service = create_workflow_service(db)
    memories = await workflow_service.list_memories(offset=offset, limit=limit)
    return [workflow_service._to_memory_response(m) for m in memories]


@router.get(
    "/workflows/memories/search",
    tags=["Memories"],
    summary="Search project memories",
    description="Search memories based on keyword overlap scoring",
    response_model=List[MemoryResponse],
)
async def search_memories(
    q: str = Query(..., min_length=1, description="Search keyword prompt"),
    limit: int = Query(5, ge=1, le=20),
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[Any]:
    workflow_service = create_workflow_service(db)
    memories = await workflow_service.search_memories(prompt=q, limit=limit)
    return [workflow_service._to_memory_response(m) for m in memories]


@router.get(
    "/workflows/memories/{project_key_or_id}",
    tags=["Memories"],
    summary="Get project memory",
    description="Get a single project memory by unique project_key or UUID id",
    response_model=MemoryResponse,
)
async def get_memory(
    project_key_or_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workflow_service = create_workflow_service(db)
    memory = await workflow_service.get_memory_by_id_or_key(project_key_or_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project memory not found",
        )
    return workflow_service._to_memory_response(memory)


@router.put(
    "/workflows/memories/{project_key_or_id}",
    tags=["Memories"],
    summary="Update project memory",
    description="Update an existing project memory's details",
    response_model=MemoryResponse,
)
async def update_memory(
    project_key_or_id: str,
    memory_update: MemoryUpdate,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workflow_service = create_workflow_service(db)
    memory = await workflow_service.update_memory(
        id_or_key=project_key_or_id,
        description=memory_update.description,
        architecture=memory_update.architecture,
        code_artifacts=memory_update.code_artifacts,
    )
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project memory not found",
        )
    return workflow_service._to_memory_response(memory)


@router.delete(
    "/workflows/memories/{project_key_or_id}",
    tags=["Memories"],
    summary="Delete project memory",
    description="Delete a project memory by project_key or UUID id",
)
async def delete_memory(
    project_key_or_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workflow_service = create_workflow_service(db)
    deleted = await workflow_service.delete_memory(project_key_or_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project memory not found",
        )
    return {"message": "Project memory deleted successfully"}


@router.get(
    "/workflows/{workflow_id}",
    tags=["Workflows"],
    summary="Get workflow",
    description="Get workflow by ID",
    response_model=WorkflowResponse,
)
async def get_workflow(
    workflow_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """
    Get workflow by ID.
    """
    workflow_service = create_workflow_service(db)
    workflow_db = await workflow_service.get(workflow_id)
    if not workflow_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return workflow_db


@router.post(
    "/workflows/{workflow_id}/execute",
    tags=["Workflows"],
    summary="Execute workflow",
    description="Execute a workflow using LangGraph agents asynchronously",
    response_model=ExecutionResponse,
)
async def execute_workflow(
    workflow_id: str,
    execution: ExecutionCreate,
    background_tasks: BackgroundTasks,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Execute workflow.
    """
    workflow_service = create_workflow_service(db)
    workflow_db = await workflow_service.get(workflow_id)
    if not workflow_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    execution_service = create_execution_service(db)
    exec_res = await execution_service.create_execution(workflow_id, execution)

    # Broadcast started event
    from apps.api.websocket.manager import get_manager
    manager = get_manager()
    await manager.broadcast(workflow_id, {
        "type": "execution.started",
        "payload": {
            "workflowId": workflow_id,
            "executionId": exec_res.id
        }
    })

    # Trigger async execution
    task_desc = workflow_db.name
    if workflow_db.inputs and workflow_db.inputs.get("prompt"):
        task_desc = workflow_db.inputs.get("prompt")
    elif workflow_db.description:
        task_desc = workflow_db.description

    background_tasks.add_task(
        run_langgraph_workflow_background,
        workflow_id=workflow_id,
        execution_id=exec_res.id,
        task_description=task_desc,
        inputs=workflow_db.inputs or {}
    )

    return exec_res


@router.get(
    "/workflows/{workflow_id}/executions",
    tags=["Workflows"],
    summary="List executions",
    description="List workflow executions",
    response_model=List[ExecutionResponse],
)
async def list_executions(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ExecutionResponse]:
    """
    List workflow executions.
    """
    execution_service = create_execution_service(db)
    return await execution_service.list_executions(workflow_id, limit)


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}",
    tags=["Workflows"],
    summary="Get execution",
    description="Get workflow execution by ID",
    response_model=ExecutionResponse,
)
async def get_execution(
    workflow_id: str,
    execution_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Get execution by ID.
    """
    execution_service = create_execution_service(db)
    execution = await execution_service.get_execution(workflow_id, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    return execution


@router.post(
    "/workflows/{workflow_id}/executions/{execution_id}/cancel",
    tags=["Workflows"],
    summary="Cancel execution",
    description="Cancel a workflow execution",
    response_model=ExecutionResponse,
)
async def cancel_execution(
    workflow_id: str,
    execution_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Cancel execution.
    """
    execution_service = create_execution_service(db)
    return await execution_service.update_execution_status(execution_id, "cancelled")


@router.post(
    "/workflows/{workflow_id}/executions/{execution_id}/retry",
    tags=["Workflows"],
    summary="Retry execution",
    description="Retry a failed workflow execution",
    response_model=ExecutionResponse,
)
async def retry_execution(
    workflow_id: str,
    execution_id: str,
    background_tasks: BackgroundTasks,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Retry execution.
    """
    workflow_service = create_workflow_service(db)
    workflow_db = await workflow_service.get(workflow_id)
    if not workflow_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    execution_service = create_execution_service(db)
    exec_res = await execution_service.create_execution(workflow_id)

    # Trigger async execution
    task_desc = workflow_db.name
    if workflow_db.inputs and workflow_db.inputs.get("prompt"):
        task_desc = workflow_db.inputs.get("prompt")
    elif workflow_db.description:
        task_desc = workflow_db.description

    background_tasks.add_task(
        run_langgraph_workflow_background,
        workflow_id=workflow_id,
        execution_id=exec_res.id,
        task_description=task_desc,
        inputs=workflow_db.inputs or {}
    )

    return exec_res


@router.post(
    "/workflows/{workflow_id}/executions/{execution_id}/resume",
    tags=["Workflows"],
    summary="Resume execution",
    description="Resume a paused workflow execution",
    response_model=ExecutionResponse,
)
async def resume_execution(
    workflow_id: str,
    execution_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Resume execution.
    """
    execution_service = create_execution_service(db)
    return await execution_service.update_execution_status(execution_id, "running")


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}/messages",
    tags=["Workflows"],
    summary="Get execution messages",
    description="Retrieve all inter-agent messages for a given execution",
)
async def get_execution_messages(
    workflow_id: str,
    execution_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    execution_service = create_execution_service(db)
    messages = await execution_service.get_execution_messages(execution_id)
    return messages


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}/download",
    tags=["Workflows"],
    summary="Download project ZIP",
    description="Download the generated project files as a deployable ZIP archive",
)
async def download_project_zip(
    workflow_id: str,
    execution_id: str,
    user: Any = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import Response
    from sqlalchemy import select
    from packages.state.models.workflow import Execution as DBExecution
    import json
    
    execution_service = create_execution_service(db)
    
    query = select(DBExecution).where(DBExecution.execution_id == execution_id)
    result = await db.execute(query)
    db_execution = result.scalar_one_or_none()
    if not db_execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    artifacts = []
    if db_execution.result:
        try:
            res_dict = json.loads(db_execution.result)
            if "code_artifacts" in res_dict:
                artifacts = res_dict["code_artifacts"]
        except Exception:
            pass
            
    if not artifacts and db_execution.checkpoint:
        try:
            chk_dict = json.loads(db_execution.checkpoint)
            if "code_artifacts" in chk_dict:
                artifacts = chk_dict["code_artifacts"]
            elif "artifacts" in chk_dict:
                artifacts = chk_dict["artifacts"]
        except Exception:
            pass
            
    zip_bytes = execution_service.package_project_zip(execution_id, artifacts)
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=project-{execution_id}.zip"
        }
    )

