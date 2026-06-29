"""Analytics API routes."""

import json
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request

from app.auth import require_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _db(request: Request):
    return request.app.state.db


async def _compute_dashboard(db, user_id: str) -> dict:
    """Internal: aggregated dashboard metrics for the current user."""
    project_count = await db.fetchval(
        "SELECT count(*) FROM projects WHERE created_by = $1", user_id,
    ) or 0

    team_count = await db.fetchval(
        "SELECT count(*) FROM teams WHERE created_by = $1", user_id,
    ) or 0

    task_counts = await db.fetch(
        "SELECT status, count(*) as cnt FROM tasks WHERE created_by = $1 GROUP BY status",
        user_id,
    )
    task_counts_map = {r["status"]: r["cnt"] for r in task_counts}
    total_tasks = sum(task_counts_map.values())

    exec_row = await db.fetchrow(
        """
        SELECT
            count(*) AS total,
            count(*) FILTER (WHERE status = 'completed') AS completed,
            count(*) FILTER (WHERE status = 'failed') AS failed,
            COALESCE(avg(duration_ms), 0) AS avg_duration_ms,
            COALESCE(sum(tokens_used), 0) AS total_tokens
        FROM executions WHERE created_by = $1
        """,
        user_id,
    )
    total_execs = exec_row["total"] if exec_row else 0
    completed_execs = exec_row["completed"] if exec_row else 0
    failed_execs = exec_row["failed"] if exec_row else 0
    avg_duration_ms = float(exec_row["avg_duration_ms"]) if exec_row else 0.0
    total_tokens = int(exec_row["total_tokens"]) if exec_row else 0
    success_rate = (completed_execs / total_execs * 100) if total_execs > 0 else 0.0

    file_count = await db.fetchval(
        "SELECT count(*) FROM project_files pf JOIN projects p ON p.id = pf.project_id WHERE p.created_by = $1",
        user_id,
    ) or 0

    key_count = await db.fetchval(
        "SELECT count(*) FROM api_keys WHERE user_id = $1", user_id,
    ) or 0

    return {
        "projects": project_count,
        "teams": team_count,
        "tasks": {"total": total_tasks, **task_counts_map},
        "executions": {
            "total": total_execs,
            "completed": completed_execs,
            "failed": failed_execs,
            "success_rate": round(success_rate, 1),
            "avg_duration_ms": round(avg_duration_ms),
        },
        "tokens": {"total": total_tokens},
        "files": file_count,
        "api_keys": key_count,
    }


async def _compute_trends(db, user_id: str, days: int) -> dict:
    """Internal: daily trends."""
    since = datetime.now(UTC) - timedelta(days=days)

    daily_execs = await db.fetch(
        """
        SELECT date_trunc('day', started_at)::date AS day,
               count(*) AS total,
               count(*) FILTER (WHERE status = 'completed') AS completed,
               count(*) FILTER (WHERE status = 'failed') AS failed,
               COALESCE(avg(duration_ms), 0) AS avg_duration_ms,
               COALESCE(sum(tokens_used), 0) AS tokens
        FROM executions
        WHERE created_by = $1 AND started_at >= $2
        GROUP BY day ORDER BY day
        """,
        user_id, since,
    )

    daily_tasks = await db.fetch(
        "SELECT date_trunc('day', created_at)::date AS day, count(*) AS cnt FROM tasks WHERE created_by = $1 AND created_at >= $2 GROUP BY day ORDER BY day",
        user_id, since,
    )

    return {
        "executions": [
            {"date": r["day"].isoformat(), "total": r["total"], "completed": r["completed"],
             "failed": r["failed"], "avg_duration_ms": round(float(r["avg_duration_ms"])), "tokens": r["tokens"]}
            for r in daily_execs
        ],
        "tasks_created": [
            {"date": r["day"].isoformat(), "count": r["cnt"]} for r in daily_tasks
        ],
    }


async def _compute_model_usage(db, user_id: str) -> list:
    """Internal: usage by model."""
    rows = await db.fetch(
        """
        SELECT model, count(*) AS total,
               count(*) FILTER (WHERE status = 'completed') AS completed,
               count(*) FILTER (WHERE status = 'failed') AS failed,
               COALESCE(avg(duration_ms), 0) AS avg_duration_ms,
               COALESCE(sum(tokens_used), 0) AS tokens
        FROM executions WHERE created_by = $1 AND model IS NOT NULL
        GROUP BY model ORDER BY total DESC
        """,
        user_id,
    )
    return [
        {"model": r["model"], "total": r["total"], "completed": r["completed"],
         "failed": r["failed"], "avg_duration_ms": round(float(r["avg_duration_ms"])),
         "tokens": r["tokens"]}
        for r in rows
    ]


async def _compute_team_performance(db, user_id: str) -> list:
    """Internal: performance by team."""
    rows = await db.fetch(
        """
        SELECT t.id, t.name, count(e.id) AS total_execs,
               count(e.id) FILTER (WHERE e.status = 'completed') AS completed,
               count(e.id) FILTER (WHERE e.status = 'failed') AS failed,
               COALESCE(avg(e.duration_ms), 0) AS avg_duration_ms,
               COALESCE(sum(e.tokens_used), 0) AS tokens
        FROM teams t
        LEFT JOIN tasks ta ON ta.team_id = t.id
        LEFT JOIN executions e ON e.task_id = ta.id
        WHERE t.created_by = $1
        GROUP BY t.id, t.name ORDER BY total_execs DESC
        """,
        user_id,
    )
    return [
        {"id": str(r["id"]), "name": r["name"], "total_execs": r["total_execs"],
         "completed": r["completed"], "failed": r["failed"],
         "avg_duration_ms": round(float(r["avg_duration_ms"])), "tokens": r["tokens"]}
        for r in rows
    ]


# â”€â”€ Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/dashboard")
async def get_dashboard_analytics(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    return await _compute_dashboard(db, user_id)


@router.get("/trends")
async def get_analytics_trends(
    request: Request,
    user_id: str = Depends(require_user),
    days: int = Query(default=30, ge=1, le=365),
):
    db = _db(request)
    return await _compute_trends(db, user_id, days)


@router.get("/models")
async def get_model_usage(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    return await _compute_model_usage(db, user_id)


@router.get("/teams")
async def get_team_performance(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    return await _compute_team_performance(db, user_id)


@router.post("/track", status_code=201)
async def track_event(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    body = await request.json()
    event_id = str(uuid.uuid4())
    await db.execute(
        """
        INSERT INTO analytics_events (id, project_id, team_id, task_id, execution_id, event_type, event_data, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        event_id,
        body.get("project_id"), body.get("team_id"), body.get("task_id"),
        body.get("execution_id"), body.get("event_type", "custom"),
        json.dumps(body.get("event_data", {})), user_id,
    )
    return {"id": event_id, "status": "tracked"}


@router.get("/export")
async def export_analytics(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    dashboard = await _compute_dashboard(db, user_id)
    trends = await _compute_trends(db, user_id, days=90)
    models = await _compute_model_usage(db, user_id)
    teams = await _compute_team_performance(db, user_id)
    return {
        "exported_at": datetime.now(tz=UTC).isoformat(),
        "dashboard": dashboard,
        "trends": trends,
        "models": models,
        "teams": teams,
    }
