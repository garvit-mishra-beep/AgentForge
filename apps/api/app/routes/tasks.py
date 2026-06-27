import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from agents.orchestrator import run_task
from app.auth import require_user
from core.task_tracker import tracker
from models.schemas import (
    TaskCreate,
    TaskMessageResponse,
    TaskResponse,
    TaskStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _db(request: Request):
    return request.app.state.db


async def _require_task_ownership(db, task_id: str, user_id: str) -> TaskResponse | None:
    row = await db.fetchrow(
        """
        SELECT id, team_id, title, description, status::text,
               created_by, created_at, updated_at, completed_at, error_message, project_id
        FROM tasks WHERE id = $1 AND created_by = $2
        """,
        task_id, user_id,
    )
    if not row:
        return None
    return TaskResponse(
        id=str(row["id"]), team_id=str(row["team_id"]),
        title=row["title"], description=row["description"],
        status=TaskStatus(row["status"]),
        created_by=str(row["created_by"]),
        created_at=row["created_at"], updated_at=row["updated_at"],
        completed_at=row["completed_at"], error_message=row["error_message"],
        project_id=str(row["project_id"]) if row["project_id"] else None,
    )


@router.post("", status_code=201)
async def create_task(
    body: TaskCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)

    # Authorization: the caller must own the target team (and project, if any).
    # Without this a user could create a task against a team/project they don't
    # own (IDOR, TOP_FINDINGS #4).
    owns_team = await db.fetchval(
        "SELECT 1 FROM teams WHERE id = $1 AND created_by = $2",
        body.team_id, user_id,
    )
    if not owns_team:
        raise HTTPException(status_code=404, detail="Team not found")

    if body.project_id:
        owns_project = await db.fetchval(
            "SELECT 1 FROM projects WHERE id = $1 AND created_by = $2",
            body.project_id, user_id,
        )
        if not owns_project:
            raise HTTPException(status_code=404, detail="Project not found")

    members = await db.fetch(
        "SELECT role::text, model FROM team_members WHERE team_id = $1",
        body.team_id,
    )
    roles = {m["role"] for m in members}
    required = {"team_lead", "builder", "reviewer"}
    missing = required - roles
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Team missing required roles: {', '.join(sorted(missing))}",
        )

    task_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO tasks (id, team_id, title, description, created_by, project_id) VALUES ($1, $2, $3, $4, $5, $6)",
        task_id, body.team_id, body.title, body.description, user_id, body.project_id,
    )

    tracker.create_task(run_task(db, task_id), name=f"task-{task_id[:8]}")

    return await _get_task_by_id(db, task_id)


@router.get("")
async def list_tasks(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = 50,
    offset: int = 0,
):
    db = _db(request)
    rows = await db.fetch(
        """
        SELECT id, team_id, title, description, status::text,
               created_by, created_at, updated_at, completed_at, error_message, project_id
        FROM tasks
        WHERE created_by = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset,
    )
    return [
        TaskResponse(
            id=str(r["id"]), team_id=str(r["team_id"]),
            title=r["title"], description=r["description"],
            status=TaskStatus(r["status"]),
            created_by=str(r["created_by"]),
            created_at=r["created_at"], updated_at=r["updated_at"],
            completed_at=r["completed_at"], error_message=r["error_message"],
            project_id=str(r["project_id"]) if r["project_id"] else None,
        )
        for r in rows
    ]


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    task = await _require_task_ownership(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/messages")
async def get_task_messages(
    task_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    task = await _require_task_ownership(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    rows = await db.fetch(
        """
        SELECT id, task_id, step_order, role::text, model,
               message_type::text, content, created_at
        FROM task_messages
        WHERE task_id = $1
        ORDER BY step_order, created_at
        """,
        task_id,
    )
    return [
        TaskMessageResponse(
            id=str(r["id"]), task_id=str(r["task_id"]),
            step_order=r["step_order"], role=r["role"],
            model=r["model"], message_type=r["message_type"],
            content=r["content"], created_at=r["created_at"],
        )
        for r in rows
    ]


async def _get_task_by_id(db, task_id: str) -> TaskResponse | None:
    row = await db.fetchrow(
        """
        SELECT id, team_id, title, description, status::text,
               created_by, created_at, updated_at, completed_at, error_message, project_id
        FROM tasks WHERE id = $1
        """,
        task_id,
    )
    if not row:
        return None
    return TaskResponse(
        id=str(row["id"]), team_id=str(row["team_id"]),
        title=row["title"], description=row["description"],
        status=TaskStatus(row["status"]),
        created_by=str(row["created_by"]),
        created_at=row["created_at"], updated_at=row["updated_at"],
        completed_at=row["completed_at"], error_message=row["error_message"],
        project_id=str(row["project_id"]) if row["project_id"] else None,
    )
