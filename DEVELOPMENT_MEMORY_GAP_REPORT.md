# Development Memory Gap Report

**Scope:** Can AgentForge remember what it has learned across sessions, across
tasks, and across a team?

**Verdict:** AgentForge has a *memory storage* layer (`agent_memories` table,
`memory_service.py`) and a *feedback flywheel* (`finding_feedback` table,
`feedback_service.py`) — both of which are genuinely well-designed. But it
does not have a *development memory graph*. The system remembers
"individual finding fingerprints the user rejected" but not "we decided not
to introduce a router because of X", "this module is fragile because of Y",
or "Alice shipped this feature last quarter and here is what we learned".

Memory today is **task-scoped** and **string-keyed**. Production development
memory is **decision-scoped** and **graph-shaped**.

---

## 1. What Exists Today

### `agent_memories` (good foundation)

Migration `009_memories.sql` defines:

- `id`, `user_id`, `project_id`, `team_id`, `task_id`, `key`, `content`,
  `memory_type`, `importance`, `tags`, `source`, `metadata`, timestamps.

Types in use: `general`, `code`, `decision`, `pattern`, `review`.
Importance is a float 0–1.
Tags are `TEXT[]` with a GIN index.

`memory_service.py` (243 lines) provides:

- `store_memory`, `get_memory`, `get_memories` (filtered list).
- `get_relevant_memories(context)` — keyword matching using `ILIKE` against
  `key`/`content`/`tags`.

### Feedback flywheel (genuine moat seed)

Migration `016_finding_feedback.sql` plus `feedback_service.py` (109 lines)
implements:

- `record_feedback(user_id, fingerprint, title, decision, …)`.
- `rejected_patterns(user_id, project_id)` — returns the user's most-rejected
  patterns.
- `format_rejected_patterns_for_prompt` — injects "don't re-raise these" hints
  into the Reviewer prompt.
- `feedback_stats(user_id)` — accept/reject counts for a dashboard.

The orchestrator wires this in (`orchestrator.py` `learned_signal` field),
and the Reviewer prompt renders `{{ learned_signal }}`. This is real, working
feedback learning — the right foundation for a moat.

### What is already weak

1. **`get_relevant_memories` is keyword-based, not embedding-based.** The
   docstring literally says "For production, this would use vector
   embeddings." The schema has `metadata JSONB` but no `embedding vector`
   column. Pgvector is enabled (referenced in `repo_contexts` migration as a
   forward declaration), but memories are not embedded.
2. **Memory retrieval is run once per task.** The orchestrator calls
   `get_relevant_memories` exactly once, before the graph starts. There is no
   per-node retrieval, no "retrieve more on demand", no "store this insight
   when we discover it mid-task".
3. **There is no decision memory.** "Why did we use Postgres over Dynamo?"
   has no home. The `memory_type='decision'` value is allowed by convention
   only; no agent or route produces them on its own.
4. **There is no feature-history memory.** The `tasks` table has
   `created_at`/`completed_at`, but no table tracks "feature X shipped on
   date Y by user Z".
5. **There is no refactoring memory.** "We refactored auth in PR #423
   because…" is not captured.
6. **Memory is per-user, not per-team.** Multi-user collaboration has no
   shared memory surface.
7. **Memory has no expiration, decay, or consolidation.** A noisy pattern is
   remembered forever unless someone deletes it. There is no "forgetting"
   mechanism.

---

## 2. Specific Gaps Ranked by Impact

### M-1 — No vector embeddings on memories (P0)

The schema is missing an `embedding vector(1536)` column on `agent_memories`.
Without it, retrieval is `ILIKE` keyword matching — which fails on synonyms
("auth" vs "authentication"), paraphrases, and concepts not present
verbatim.

**Effort:** 1 week. Migration 019 + replace `get_relevant_memories` with
`<=>` cosine distance. Pick a default embedder (`text-embedding-3-small`).

### M-2 — No decision-tracking surface (P0)

The system has no route or table that records *why* a change was made. The
PRD claims agents collaborate like a real team; real teams write ADRs and
capture them.

**Effort:** 2 weeks. Add:

- `decisions` table: id, project_id, author_id, title, context, decision,
  consequences, status (proposed/accepted/superseded), superseded_by,
  created_at.
- Capture point: when a Task's `delivery.verdict` is `pass` and the Builder
  changed > N files, prompt the Team Lead to write an ADR.
- Route: `GET/POST /api/v1/decisions`, `GET /api/v1/decisions/:id`.

### M-3 — No feature-history surface (P0)

There is no query like "what features did this team ship in Q2?" The `tasks`
table has titles, but titles are not normalized to features.

**Effort:** 1 week.

- Add `features` table: id, project_id, name, description, status
  (planned/in_progress/shipped/abandoned), first_task_id, last_task_id,
  shipped_at.
- When the Team Lead creates a plan, it can declare a `feature_id`. Tasks
  within the plan inherit it.

### M-4 — No refactoring memory (P1)

The Builder has no way to ask "have we tried refactoring this before?" and
the Team Lead has no way to record "this refactor went well/poorly".

**Effort:** 1 week. Use the existing `agent_memories` with a new type
`refactor` and a structured schema.

### M-5 — Memory retrieval is a one-shot at task start (P1)

The orchestrator pulls memories once before the graph runs. There is no
"the builder is now writing a test for `auth.py` — pull memories about
testing auth". Mid-graph retrieval would materially improve quality.

**Effort:** 2 weeks. Add a small `retrieve()` helper usable from inside any
node, with caching.

### M-6 — No shared team memory (P1)

Today memories are scoped to `user_id`. A team of three developers all
benefit from the same prior decisions, but each user has to trigger their
own review to learn anything.

**Effort:** 1 week. Add a `team_id`-only scope (`NULL user_id, NOT NULL
team_id`) and a `share_with_team(memory_id)` route. The orchestrator already
queries `team_id`; pull both.

### M-7 — No memory consolidation / decay (P2)

Memory never expires. Important findings sit next to trivial chatter.

**Effort:** 1 week. Background job: decay `importance` by 1% per week;
collapse near-duplicate memories by `fingerprint` similarity.

### M-8 — No "memory viewer" semantic search (P2)

The web has `components/memory-viewer.tsx` (10k lines) but it lists
memories, not searches them. Semantic search requires M-1 first.

---

## 3. What is Already Good

- The `finding_feedback` flywheel is a real, working learning loop. Few
  products have this.
- `memory_service.py` is small and readable — not over-engineered.
- Tags are properly indexed (GIN).
- Importance ranking works (`ORDER BY importance DESC`).
- Sanitization (`wrap_memories`) already fences memory content against
  prompt injection.

---

## 4. Architecture Recommendations

1. **Add embeddings now.** Migration 019. Use pgvector's HNSW index for
   sub-100ms retrieval.
2. **Decisions table + route.** Decisions are first-class objects, not
   memory entries.
3. **Features table.** Track what shipped, when, by whom.
4. **Mid-graph retrieval.** Add a `retrieve(state, query)` helper used by
   Builder/Reviewer/Architect when they need fresh context.
5. **Team-scope memory.** Add `team_id`-only rows.
6. **Memory decay background job.** Use `apscheduler` or a simple async
   task.

---

## 5. Metrics for "Done"

| Metric | Target |
|--------|--------|
| Vector retrieval p95 latency | <50ms over 100k memories |
| Decision captured per shipped feature | ≥1 |
| Mid-graph retrieval hits per task | 2–5 |
| Memory retention after 30 days of decay | Top 10% of memories retained at >0.5 importance |
| Team-scope memory utilization | ≥30% of tasks |

---

## 6. Honest Assessment

The flywheel is real and rare. Most "AI coding tools" have no feedback loop at
all. AgentForge has one, and it is wired in.

What is missing is **shape**. Memories today are flat key-value strings.
Production development memory is a *graph of decisions and consequences*,
where the nodes are decisions, features, and refactors, and the edges are
"supersedes", "implements", "contradicts", "builds on".

The path from here to "real development memory" requires (a) embeddings, (b)
two new tables (decisions, features), and (c) one new background job
(decay). It is a 4–6 week P0 effort, and it is the second-highest leverage
investment in the entire roadmap, behind only the repository intelligence
graph itself.