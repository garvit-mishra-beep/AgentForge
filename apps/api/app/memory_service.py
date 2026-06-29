"""
Long-Term Memory Service
Stores, retrieves, and ranks memories for cross-session context.
"""

import json
import logging
import uuid
from typing import Any

from core.database import DatabasePool

logger = logging.getLogger(__name__)


async def _get_embedding(text: str, user_id: str, project_id: str | None, db: Any) -> list[float] | None:
    """Generate embedding for the text if a provider is configured, otherwise return None."""
    try:
        from core.providers import get_provider_for_user
        provider, provider_type = await get_provider_for_user("text-embedding-3-small", user_id, project_id, db)
        if provider_type == "openai":
            client = await provider._get_client()  # type: ignore[attr-defined]
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
    except Exception as e:
        logger.debug("Could not generate embedding, using keyword fallback: %s", e)
    return None


_has_embedding_column: bool | None = None


async def _check_embedding_column(db: DatabasePool) -> bool:
    global _has_embedding_column
    if _has_embedding_column is not None:
        return _has_embedding_column
    try:
        column_exists = await db.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'agent_memories' AND column_name = 'embedding'
            )
            """
        )
        _has_embedding_column = bool(column_exists)
    except Exception as e:
        logger.warning("Error checking embedding column: %s", e)
        _has_embedding_column = False
    return _has_embedding_column


async def store_memory(
    db: DatabasePool,
    user_id: str,
    key: str,
    content: str,
    memory_type: str = "general",
    importance: float = 0.5,
    tags: list[str] | None = None,
    project_id: str | None = None,
    team_id: str | None = None,
    task_id: str | None = None,
    source: str = "",
    metadata: dict | None = None,
) -> str:
    """Store a memory."""
    has_emb = await _check_embedding_column(db)
    embedding = await _get_embedding(content, user_id, project_id, db) if has_emb else None
    mem_id = str(uuid.uuid4())
    if has_emb:
        await db.execute(
            """
            INSERT INTO agent_memories (id, user_id, project_id, team_id, task_id, key, content, memory_type, importance, tags, source, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            mem_id, user_id, project_id, team_id, task_id, key, content,
            memory_type, importance, tags or [], source,
            json.dumps(metadata or {}), embedding,
        )
    else:
        await db.execute(
            """
            INSERT INTO agent_memories (id, user_id, project_id, team_id, task_id, key, content, memory_type, importance, tags, source, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            mem_id, user_id, project_id, team_id, task_id, key, content,
            memory_type, importance, tags or [], source,
            json.dumps(metadata or {}),
        )
    return mem_id


async def get_memory(db: DatabasePool, memory_id: str, user_id: str) -> dict | None:
    """Get a single memory by ID."""
    row = await db.fetchrow(
        "SELECT * FROM agent_memories WHERE id = $1 AND user_id = $2",
        memory_id, user_id,
    )
    return _row_to_dict(row) if row else None


async def get_memories(
    db: DatabasePool,
    user_id: str,
    project_id: str | None = None,
    team_id: str | None = None,
    memory_type: str | None = None,
    key: str | None = None,
    tags: list[str] | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    min_importance: float = 0.0,
) -> list[dict]:
    """Query memories with filters."""
    conditions = ["user_id = $1"]
    params: list[Any] = [user_id]
    idx = 2

    if project_id:
        conditions.append(f"project_id = ${idx}")
        params.append(project_id)
        idx += 1
    if team_id:
        conditions.append(f"team_id = ${idx}")
        params.append(team_id)
        idx += 1
    if memory_type:
        conditions.append(f"memory_type = ${idx}")
        params.append(memory_type)
        idx += 1
    if key:
        conditions.append(f"key = ${idx}")
        params.append(key)
        idx += 1
    if search:
        conditions.append(f"content ILIKE ${idx}")
        params.append(f"%{search}%")
        idx += 1
    if tags:
        conditions.append(f"tags && ${idx}")  # array overlap
        params.append(tags)
        idx += 1

    conditions.append(f"importance >= ${idx}")
    params.append(min_importance)
    idx += 1

    query = f"""
        SELECT * FROM agent_memories
        WHERE {' AND '.join(conditions)}
        ORDER BY importance DESC, created_at DESC
        LIMIT ${idx}
        OFFSET ${idx + 1}
    """
    params.append(limit)
    params.append(offset)

    rows = await db.fetch(query, *params)
    return [_row_to_dict(r) for r in rows]


async def get_relevant_memories(
    db: DatabasePool,
    user_id: str,
    context: str,
    project_id: str | None = None,
    team_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Get relevant memories based on vector similarity or keyword matching.
    """
    has_emb = await _check_embedding_column(db)
    embedding = await _get_embedding(context, user_id, project_id, db) if has_emb else None

    conditions = ["user_id = $1"]
    params: list[Any] = [user_id]
    idx = 2

    if project_id:
        conditions.append(f"project_id = ${idx}")
        params.append(project_id)
        idx += 1
    if team_id:
        conditions.append(f"team_id = ${idx}")
        params.append(team_id)
        idx += 1

    if has_emb and embedding is not None:
        params.append(embedding)
        query = f"""
            SELECT *, 1 - (embedding <=> ${idx}) as similarity
            FROM agent_memories
            WHERE {' AND '.join(conditions)} AND embedding IS NOT NULL
            ORDER BY similarity DESC, importance DESC
            LIMIT ${idx + 1}
        """
        params.append(limit)
        rows = await db.fetch(query, *params)
        return [_row_to_dict(r) for r in rows]

    # Fallback to keyword matching
    keywords = [w.strip().lower() for w in context.split() if len(w.strip()) > 3]

    if not keywords:
        return []

    # Keyword matching against key, content, and tags
    kw_conditions = []
    for kw in keywords:
        kw_conditions.append(f"(key ILIKE ${idx} OR content ILIKE ${idx} OR array_to_string(tags, ' ') ILIKE ${idx})")
        params.append(f"%{kw}%")
        idx += 1

    if kw_conditions:
        conditions.append(f"({' OR '.join(kw_conditions)})")

    query = f"""
        SELECT * FROM agent_memories
        WHERE {' AND '.join(conditions)}
        ORDER BY importance DESC, created_at DESC
        LIMIT ${idx}
    """
    params.append(limit)

    rows = await db.fetch(query, *params)
    return [_row_to_dict(r) for r in rows]


async def update_memory(
    db: DatabasePool,
    memory_id: str,
    user_id: str,
    content: str | None = None,
    importance: float | None = None,
    tags: list[str] | None = None,
) -> bool:
    """Update a memory's content, importance, or tags."""
    existing = await db.fetchrow(
        "SELECT id FROM agent_memories WHERE id = $1 AND user_id = $2",
        memory_id, user_id,
    )
    if not existing:
        return False

    sets = []
    params: list[Any] = []
    idx = 1
    if content is not None:
        sets.append(f"content = ${idx}")
        params.append(content)
        idx += 1
    if importance is not None:
        sets.append(f"importance = ${idx}")
        params.append(importance)
        idx += 1
    if tags is not None:
        sets.append(f"tags = ${idx}")
        params.append(tags)
        idx += 1

    if not sets:
        return True

    sets.append("updated_at = NOW()")
    params.append(memory_id)
    await db.execute(
        f"UPDATE agent_memories SET {', '.join(sets)} WHERE id = ${idx}",
        *params,
    )
    return True


async def delete_memory(db: DatabasePool, memory_id: str, user_id: str) -> bool:
    """Delete a memory."""
    result = await db.execute(
        "DELETE FROM agent_memories WHERE id = $1 AND user_id = $2",
        memory_id, user_id,
    )
    return result != "DELETE 0"


async def delete_memories_by_project(db: DatabasePool, project_id: str, user_id: str) -> int:
    """Delete all memories for a project."""
    result = await db.execute(
        "DELETE FROM agent_memories WHERE project_id = $1 AND user_id = $2",
        project_id, user_id,
    )
    return int(result.split()[-1]) if result else 0


def _row_to_dict(row) -> dict:
    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]),
        "project_id": str(row["project_id"]) if row.get("project_id") else None,
        "team_id": str(row["team_id"]) if row.get("team_id") else None,
        "task_id": str(row["task_id"]) if row.get("task_id") else None,
        "key": row["key"],
        "content": row["content"],
        "memory_type": row["memory_type"],
        "importance": float(row["importance"]),
        "tags": list(row["tags"]) if row.get("tags") else [],
        "source": row["source"],
        "metadata": row.get("metadata") or {},
        "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        "updated_at": row["updated_at"].isoformat() if hasattr(row["updated_at"], "isoformat") else str(row["updated_at"]),
    }
