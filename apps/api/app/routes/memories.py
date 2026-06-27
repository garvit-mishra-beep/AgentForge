"""Long-Term Memory API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import require_user
from app.memory_service import (
    delete_memory,
    get_memories,
    get_memory,
    get_relevant_memories,
    store_memory,
    update_memory,
)

router = APIRouter(prefix="/memories", tags=["memories"])


def _db(request: Request):
    return request.app.state.db


@router.get("")
async def list_memories(
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str = Query(default=""),
    team_id: str = Query(default=""),
    memory_type: str = Query(default=""),
    key: str = Query(default=""),
    search: str = Query(default=""),
    tags: str = Query(default=""),
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    db = _db(request)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    return await get_memories(
        db, user_id,
        project_id=project_id or None,
        team_id=team_id or None,
        memory_type=memory_type or None,
        key=key or None,
        search=search or None,
        tags=tag_list,
        limit=limit,
        offset=offset,
        min_importance=min_importance,
    )


@router.get("/relevant")
async def relevant_memories(
    request: Request,
    user_id: str = Depends(require_user),
    context: str = Query(...),
    project_id: str = Query(default=""),
    team_id: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=50),
):
    db = _db(request)
    return await get_relevant_memories(
        db, user_id, context,
        project_id=project_id or None,
        team_id=team_id or None,
        limit=limit,
    )


@router.get("/{memory_id}")
async def get_memory_by_id(
    memory_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    mem = await get_memory(db, memory_id, user_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    return mem


@router.post("", status_code=201)
async def create_memory(
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    body = await request.json()
    mem_id = await store_memory(
        db, user_id,
        key=body["key"],
        content=body["content"],
        memory_type=body.get("memory_type", "general"),
        importance=body.get("importance", 0.5),
        tags=body.get("tags"),
        project_id=body.get("project_id"),
        team_id=body.get("team_id"),
        task_id=body.get("task_id"),
        source=body.get("source", ""),
        metadata=body.get("metadata"),
    )
    return {"id": mem_id, "status": "stored"}


@router.put("/{memory_id}")
async def update_memory_by_id(
    memory_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    body = await request.json()
    ok = await update_memory(
        db, memory_id, user_id,
        content=body.get("content"),
        importance=body.get("importance"),
        tags=body.get("tags"),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "updated"}


@router.delete("/{memory_id}", status_code=204)
async def delete_memory_by_id(
    memory_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    ok = await delete_memory(db, memory_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
