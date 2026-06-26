from fastapi import APIRouter, Depends, HTTPException, Request, Query

from app.auth import require_user
from models.schemas import ExecutionResponse

router = APIRouter(prefix="/executions", tags=["executions"])


def _db(request: Request):
    return request.app.state.db


@router.get("/detail/{exec_id}")
async def get_execution_by_id(
    exec_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    row = await db.fetchrow(
        """
        SELECT e.id, e.task_id, e.status::text, e.current_node,
               e.started_at, e.completed_at, e.error_message
        FROM executions e
        JOIN tasks t ON t.id = e.task_id
        WHERE e.id = $1 AND t.created_by = $2
        """,
        exec_id, user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionResponse(
        id=str(row["id"]), task_id=str(row["task_id"]),
        status=row["status"], current_node=row["current_node"],
        started_at=row["started_at"], completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.get("/{task_id}")
async def get_execution(
    task_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    row = await db.fetchrow(
        """
        SELECT e.id, e.task_id, e.status::text, e.current_node,
               e.started_at, e.completed_at, e.error_message
        FROM executions e
        JOIN tasks t ON t.id = e.task_id
        WHERE e.task_id = $1 AND t.created_by = $2
        """,
        task_id, user_id,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Execution not found for this task",
        )

    return ExecutionResponse(
        id=str(row["id"]), task_id=str(row["task_id"]),
        status=row["status"], current_node=row["current_node"],
        started_at=row["started_at"], completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.get("")
async def list_executions(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    db = _db(request)
    rows = await db.fetch(
        """
        SELECT e.id, e.task_id, e.status::text, e.current_node,
               e.started_at, e.completed_at, e.error_message
        FROM executions e
        JOIN tasks t ON t.id = e.task_id
        WHERE t.created_by = $1
        ORDER BY e.started_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset,
    )
    return [
        ExecutionResponse(
            id=str(r["id"]), task_id=str(r["task_id"]),
            status=r["status"], current_node=r["current_node"],
            started_at=r["started_at"], completed_at=r["completed_at"],
            error_message=r["error_message"],
        )
        for r in rows
    ]
