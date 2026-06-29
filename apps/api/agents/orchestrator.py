import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from agents.graph import build_graph
from app.memory_service import get_relevant_memories, store_memory
from app.routes.tasks import ws_manager
from core.config import settings

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _reduce_context_messages(messages: list) -> list:
    if not settings.fast_demo_mode:
        return messages
    ctx = settings.max_context_messages
    return messages[-ctx:] if len(messages) > ctx else messages


async def _fetch_repository_context(db, project_id: str, user_id: str, limit: int = 30) -> str:
    """Fetch relevant code chunks and symbols from the repository context."""
    try:
        chunks = await db.fetch(
            """
            SELECT cc.content, cc.name, cc.chunk_type, pf.filename
            FROM code_chunks cc
            JOIN repository_contexts rc ON rc.id = cc.context_id
            JOIN project_files pf ON pf.id = rc.file_id
            JOIN projects p ON p.id = rc.project_id
            WHERE rc.project_id = $1 AND p.created_by = $2
            ORDER BY cc.tokens_estimate DESC
            LIMIT $3
            """,
            project_id, user_id, limit,
        )

        if not chunks:
            return ""

        parts = []
        for c in chunks:
            filename = c["filename"]
            chunk_type = c["chunk_type"]
            name = c["name"]
            content = c["content"][:500]
            parts.append(f"[{filename}] {chunk_type}: {name}\n{content}")

        return "\n\n".join(parts)
    except Exception as e:
        logger.warning("Failed to fetch repository context: %s", e)
        return ""


async def run_task(db, task_id: str) -> None:
    logger.info("Starting task %s", task_id)

    try:
        task_row = await db.fetchrow(
            "SELECT id, team_id, title, description, project_id, created_by FROM tasks WHERE id = $1",
            task_id,
        )
        if not task_row:
            logger.error("Task %s not found", task_id)
            return

        user_id = str(task_row["created_by"]) if task_row["created_by"] else None
        project_id = str(task_row["project_id"]) if task_row["project_id"] else None

        members = await db.fetch(
            "SELECT role::text, model FROM team_members WHERE team_id = $1",
            task_row["team_id"],
        )
        team_config = {m["role"]: {"role": m["role"], "model": m["model"]} for m in members}

        await db.execute(
            "UPDATE tasks SET status = 'running', updated_at = NOW() WHERE id = $1",
            task_id,
        )
        # Notify WebSocket clients of task status change to running
        await ws_manager.task_status_update(task_id, "running", None)

        exec_id = await db.fetchval(
            "INSERT INTO executions (task_id) VALUES ($1) RETURNING id",
            task_id,
        )

        # â”€â”€ Gather context and memories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        repository_context = ""
        relevant_memories = []
        learned_signal = ""

        if project_id and user_id:
            repository_context = await _fetch_repository_context(db, project_id, user_id)

        if user_id:
            try:
                relevant_memories = await get_relevant_memories(
                    db, user_id,
                    context=task_row["description"],
                    project_id=project_id,
                    team_id=str(task_row["team_id"]) if task_row["team_id"] else None,
                    limit=10,
                )
            except Exception as e:
                logger.warning("Failed to fetch memories: %s", e)

            try:
                from app.feedback_service import (
                    format_rejected_patterns_for_prompt,
                    rejected_patterns,
                )
                patterns = await rejected_patterns(db, user_id, project_id)
                learned_signal = format_rejected_patterns_for_prompt(patterns)
            except Exception as e:
                logger.warning("Failed to fetch learned signal: %s", e)

        # â”€â”€ Build initial state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        initial_state = {
            "task": {
                "id": task_row["id"],
                "title": task_row["title"],
                "description": task_row["description"],
            },
            "team_config": team_config,
            "plan": None,
            "planner_output": None,
            "builder_output": None,
            "review": None,
            "tester_output": None,
            "security_output": None,
            "architect_output": None,
            "deployment_output": None,
            "aggregator_output": None,
            "delivery": None,
            "current_step": "team_lead_plan",
            "messages": [],
            "errors": [],
            "fast_demo_mode": settings.fast_demo_mode,
            "timed_out_agents": [],
            "repository_context": repository_context,
            "relevant_memories": [
                {"key": m["key"], "content": m["content"], "memory_type": m["memory_type"], "importance": m["importance"]}
                for m in relevant_memories
            ],
            "learned_signal": learned_signal,
            # BYOK fields - pass user and project context to agent nodes
            "user_id": user_id,
            "project_id": project_id,
            # Database session for provider lookup
            "db": db,
        }

        graph = build_graph()

        # â”€â”€ Stream graph â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        step_order = 0
        final_state = dict(initial_state)

        async for event in graph.astream(initial_state):
            for node_name, state_update in event.items():
                step_order += 1
                final_state.update(state_update)
                messages = state_update.get("messages", [])
                state_update.pop("messages", None)

                if messages:
                    for msg in messages:
                        await db.execute(
                            """
                            INSERT INTO task_messages
                            (task_id, step_order, role, model, message_type, content, metadata)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            task_id, step_order, msg["role"], msg["model"],
                            msg["message_type"], msg["content"],
                            json.dumps(msg.get("metadata", {})),
                        )
                        # Send WebSocket notification for agent message
                        await ws_manager.agent_message(
                            task_id,
                            msg["content"],
                            msg["role"],
                            msg["model"],
                            len(msg.get("content", ""))  # Using length as a simple chunk index approximation
                        )

                        # Also send as execution log if it's a significant message
                        if msg["message_type"] in ["plan", "code", "review", "delivery"]:
                            await ws_manager.execution_log(
                                task_id,
                                msg["role"],  # node
                                msg["content"]  # data
                            )

                await db.execute(
                    """
                    UPDATE executions
                    SET graph_state = $1, current_node = $2
                    WHERE id = $3
                    """,
                    json.dumps(state_update, default=str),
                    node_name, exec_id,
                )

        # â”€â”€ Store execution results as memories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if user_id:
            await _store_execution_memories(db, task_row, final_state, user_id, project_id)

        # â”€â”€ Mark complete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        await db.execute(
            "UPDATE tasks SET status = 'completed', completed_at = $1, updated_at = NOW() WHERE id = $2",
            _utcnow(), task_id,
        )
        await db.execute(
            "UPDATE executions SET status = 'completed', completed_at = $1 WHERE id = $2",
            _utcnow(), exec_id,
        )

        # Notify WebSocket clients of task completion
        await ws_manager.task_status_update(task_id, "completed", None)

        logger.info("Task %s completed successfully", task_id)

    except TimeoutError:
        logger.error("Task %s timed out after %ss", task_id, settings.max_execution_time)
        await db.execute(
            "UPDATE tasks SET status = 'failed', error_message = 'Execution timed out', updated_at = NOW() WHERE id = $1",
            task_id,
        )
        await db.execute(
            "UPDATE executions SET status = 'failed', error_message = $1, completed_at = NOW() WHERE task_id = $2",
            str(settings.max_execution_time), task_id,
        )
        # Notify WebSocket clients of task timeout
        await ws_manager.task_status_update(task_id, "failed", "timeout")
    except asyncio.CancelledError:
        logger.warning("Task %s cancelled during shutdown", task_id)
        await db.execute(
            "UPDATE tasks SET status = 'failed', error_message = 'Task cancelled on server shutdown', updated_at = NOW() WHERE id = $1",
            task_id,
        )
        if 'exec_id' in locals():
            await db.execute(
                "UPDATE executions SET status = 'failed', error_message = 'Cancelled on shutdown', completed_at = NOW() WHERE id = $1",
                exec_id,
            )
        await ws_manager.task_status_update(task_id, "failed", "cancelled")
        raise
    except Exception as e:
        logger.exception("Task %s failed", task_id)
        await db.execute(
            "UPDATE tasks SET status = 'failed', error_message = $1, updated_at = NOW() WHERE id = $2",
            str(e), task_id,
        )
        await db.execute(
            "UPDATE executions SET status = 'failed', error_message = $1, completed_at = NOW() WHERE task_id = $2",
            str(e), task_id,
        )
        # Notify WebSocket clients of task failure
        await ws_manager.task_status_update(task_id, "failed", str(e))


async def _store_execution_memories(db, task_row, final_state: dict, user_id: str, project_id: str | None):
    """Store key execution outputs as memories for future reuse."""
    memories: list[dict[str, Any]] = []

    # Planning approach
    plan = final_state.get("plan")
    if plan and plan != "None":
        try:
            plan_data = json.loads(plan) if isinstance(plan, str) else plan
            plan_summary = plan_data.get("plan_summary", "") if isinstance(plan_data, dict) else ""
            if plan_summary:
                memories.append({
                    "key": f"task/{task_row['id']}/plan",
                    "content": f"Plan for task '{task_row['title']}': {plan_summary}",
                    "memory_type": "decision",
                    "importance": 0.7,
                    "tags": ["plan", f"task:{task_row['id']}"],
                })
        except (json.JSONDecodeError, TypeError):
            pass

    # Builder output summary
    builder_out = final_state.get("builder_output")
    if builder_out and builder_out != "None" and len(str(builder_out)) > 50:
        memories.append({
            "key": f"task/{task_row['id']}/implementation",
            "content": f"Implementation for task '{task_row['title']}': {str(builder_out)[:300]}",
            "memory_type": "code",
            "importance": 0.8,
            "tags": ["implementation", f"task:{task_row['id']}"],
        })

    # Review findings
    review = final_state.get("review")
    if review and review != "None":
        try:
            review_data = json.loads(review) if isinstance(review, str) else review
            if isinstance(review_data, dict):
                findings = review_data.get("findings", [])
                if findings:
                    summaries = [f.get("description", "")[:100] for f in findings[:5]]
                    memories.append({
                        "key": f"task/{task_row['id']}/review",
                        "content": f"Review findings for '{task_row['title']}': {'; '.join(summaries)}",
                        "memory_type": "pattern",
                        "importance": 0.6,
                        "tags": ["review", f"task:{task_row['id']}"],
                    })
        except (json.JSONDecodeError, TypeError):
            pass

    # Delivery summary
    delivery = final_state.get("delivery")
    if delivery and delivery != "None" and len(str(delivery)) > 30:
        try:
            delivery_data = json.loads(delivery) if isinstance(delivery, str) else delivery
            if isinstance(delivery_data, dict):
                summary = delivery_data.get("delivery_summary", "")[:300] or str(delivery_data)[:300]
                memories.append({
                    "key": f"task/{task_row['id']}/delivery",
                    "content": f"Delivery for '{task_row['title']}': {summary}",
                    "memory_type": "general",
                    "importance": 0.9,
                    "tags": ["delivery", f"task:{task_row['id']}"],
                })
        except (json.JSONDecodeError, TypeError):
            memories.append({
                "key": f"task/{task_row['id']}/delivery",
                "content": f"Output for '{task_row['title']}'",
                "memory_type": "general",
                "importance": 0.5,
                "tags": ["delivery", f"task:{task_row['id']}"],
            })

    # Store all memories
    for mem in memories:
        try:
            await store_memory(
                db, user_id,
                key=mem["key"],
                content=mem["content"],
                memory_type=mem["memory_type"],
                importance=mem["importance"],
                tags=mem["tags"],
                project_id=project_id,
                task_id=task_row["id"],
                source="agent_orchestrator",
            )
        except Exception as e:
            logger.warning("Failed to store memory '%s': %s", mem["key"], e)

    if memories:
        logger.info("Stored %d memories from execution", len(memories))
