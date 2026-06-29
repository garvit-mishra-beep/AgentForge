import logging
import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.auth import require_user, validate_websocket_token
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


# WebSocket connection manager for task updates
class TaskWebSocketManager:
    def __init__(self):
        # Map task_id to set of WebSocket connections
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections[task_id])}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")
                    disconnected.add(websocket)

            # Remove disconnected clients
            for ws in disconnected:
                self.active_connections[task_id].discard(ws)

    async def task_status_update(self, task_id: str, status: str, details: str | None = None):
        """Send task status update to connected clients."""
        message = {
            "type": "task_status_update",
            "payload": {
                "task_id": task_id,
                "status": status,
                "details": details
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        await self.broadcast_to_task(task_id, message)

    async def agent_message(self, task_id: str, content: str, role: str, model: str, chunk_index: int):
        """Send agent message (streaming content) to connected clients."""
        message = {
            "type": "agent_message",
            "payload": {
                "task_id": task_id,
                "content": content,
                "role": role,
                "model": model,
                "chunk_index": chunk_index
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        await self.broadcast_to_task(task_id, message)

    async def execution_log(self, task_id: str, node: str, data: str):
        """Send execution log to connected clients."""
        message = {
            "type": "execution_log",
            "payload": {
                "task_id": task_id,
                "node": node,
                "data": data
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        await self.broadcast_to_task(task_id, message)


# Global WebSocket manager instance
ws_manager = TaskWebSocketManager()


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

    from agents.orchestrator import run_task
    tracker.create_task(run_task(db, task_id), name=f"task-{task_id[:8]}")

    return await _get_task_by_id(db, task_id)


@router.get("")
async def list_tasks(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = Query(default=50, ge=1, le=200),
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


@router.websocket("/{task_id}/ws")
async def task_websocket_endpoint(
    websocket: WebSocket,
    task_id: str,
    request: Request,
):
    """WebSocket endpoint for real-time task updates."""
    # Extract token from query parameters or cookies for authentication
    token = websocket.query_params.get("token")
    if not token:
        # Fallback to checking cookies (for same-origin requests)
        cookie_header = websocket.headers.get('cookie', '')
        if cookie_header:
            cookies = dict(cookie.split('=', 1) for cookie in cookie_header.split('; ') if '=' in cookie)
            token = cookies.get('agentforge_token')

    # Verify the token
    user_id = None
    if token:
        user_id = await validate_websocket_token(token)

    # If no token in query/cookies, try to get from headers (less common for WS but possible)
    if not user_id:
        auth_header = websocket.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            user_id = await validate_websocket_token(token)

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    # Verify task ownership
    db = _db(request)
    task = await _require_task_ownership(db, task_id, user_id)
    if not task:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found or access denied")
        return

    # Connect the WebSocket
    await ws_manager.connect(websocket, task_id)

    try:
        # Keep connection alive and handle incoming messages (if any)
        while True:
            # We primarily send data to client, but listen for disconnect
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        ws_manager.disconnect(websocket, task_id)


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
