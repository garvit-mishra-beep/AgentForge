# Agent Memory — AgentForge

**Last Updated:** June 2026

---

## Architecture Overview

AgentForge implements two tiers of agent memory:

| Memory Type | Scope | Duration | Storage | Retrieval |
|-------------|-------|----------|---------|-----------|
| Short-term | Single task run | Task lifetime | LangGraph `AgentState` TypedDict | Direct state access |
| Long-term | Cross-task, per project | 180 days | `agent_memories` table (pgvector) | Cosine similarity search |

---

## Short-Term Memory (LangGraph State)

The `AgentState` TypedDict persists across all nodes within a single task execution:

```python
from typing import TypedDict, Optional

class AgentState(TypedDict):
    # Identity
    task_id: str
    project_id: str
    team_id: str

    # Input
    task: str                             # Original task description
    codebase_summary: str                 # Auto-generated codebase context
    acceptance_criteria: list[str]        # From Team Lead plan

    # Execution
    current_step: str                     # Current phase identifier
    step_order: int                       # Monotonically increasing step counter
    plan: Optional[dict]                  # Team Lead's structured plan
    agent_outputs: dict[str, dict]        # { role_name: { files, summary, ... } }
    review_feedback: Optional[dict]       # Reviewer's structured feedback
    test_results: Optional[dict]          # QA test results
    security_findings: Optional[dict]     # Security audit findings

    # Control
    errors: list[dict]                    # { step, error_type, message, recovery }
    retry_count: int                      # Current retry attempt number
    max_retries: int = 3                  # Configurable per task

    # Tracking
    total_tokens: int
    total_cost: float
    started_at: str                       # ISO 8601
```

Fields that persist across **all** nodes: `task_id`, `project_id`, `team_id`, `task`, `codebase_summary`, `plan`, `current_step`, `agent_outputs`, `errors`, `total_tokens`, `total_cost`.

Fields that are **node-specific**: `review_feedback` (written by Reviewer, read by Backend), `test_results` (written by QA, read by Security).

---

## Long-Term Memory (pgvector)

### Storage Schema

```sql
CREATE TABLE agent_memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    task_id     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role        VARCHAR(50) NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(1536) NOT NULL,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Embedding Generation

- **Model:** `text-embedding-3-small` (OpenAI)
- **Dimensions:** 1536
- **Trigger:** On task completion — the Team Lead's delivery summary is embedded and stored
- **Content stored:** Task title + description + delivery summary + key file paths

```python
async def store_memory(agent_id, task_id, project_id, role, content):
    embedding = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=content,
    )
    await db.execute("""
        INSERT INTO agent_memories (agent_id, task_id, project_id, role, content, embedding)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, agent_id, task_id, project_id, role, content, embedding.data[0].embedding)
```

### Retrieval Strategy

```python
async def retrieve_memories(agent_id: str, query: str, project_id: str, top_k: int = 5) -> list[dict]:
    # Generate embedding for the query
    query_embedding = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )

    # Cosine similarity search with threshold
    rows = await db.fetch("""
        SELECT content, metadata, role, created_at,
               1 - (embedding <=> $1) AS similarity
        FROM agent_memories
        WHERE project_id = $2
          AND 1 - (embedding <=> $1) >= 0.82   -- similarity threshold
        ORDER BY similarity DESC
        LIMIT $3
    """, query_embedding, project_id, top_k)

    return [dict(r) for r in rows]
```

### Threshold

| Similarity Score | Action |
|-----------------|--------|
| ≥ 0.90 | Include as "highly relevant past context" |
| 0.82 – 0.89 | Include as "possibly relevant context" |
| < 0.82 | Discard — not sufficiently relevant |

### Memory Injection Format

Retrieved memories are injected into the agent's context as:

```
PREVIOUSLY RELEVANT TASKS:
1. [Task: "Build JWT Authentication" | Similarity: 0.94]
   Summary: Implemented JWT auth service with login/refresh endpoints,
   refresh token rotation, and session invalidation.
   Files: app/services/auth.py, app/routes/auth.py

2. [Task: "Add Password Reset Flow" | Similarity: 0.87]
   Summary: Created password reset with email token, expiry, and
   rate-limiting. Modified: app/routes/auth.py, app/services/user.py
```

### Memory Write Triggers

| Event | Action |
|-------|--------|
| Task completed successfully | Store Team Lead delivery summary as agent memory |
| Task failed after all retries | Store error summary (for learning from failures) |
| Human provides revision feedback | Store revision notes as agent memory |

### Memory Pruning

| Condition | Action |
|-----------|--------|
| Memory age > 180 days | Soft-delete (flag as `archived = true`) |
| > 10,000 memories per agent | Summarize oldest 5,000 into a single compressed entry, delete originals |
| Project deleted | Cascade delete all project memories |

---

## Shared Team Memory

All agents on the same team can read memories written by other agents on the same team. This is controlled by the `project_id` scope — a query for relevant memories returns entries from all agents within that project.

This means:
- Backend Engineer can learn from a previous Security Engineer's findings
- QA Engineer can reference past test patterns written by another QA agent
- Team Lead has full visibility into all agent memories for context

---

## Implementation Files

| File | Purpose |
|------|---------|
| `apps/api/agents/memory/store.py` | Memory writing logic |
| `apps/api/agents/memory/retrieve.py` | Memory retrieval with pgvector query |
| `apps/api/agents/memory/prune.py` | Scheduled pruning job |
| `tests/test_memory.py` | Unit tests for memory operations |
