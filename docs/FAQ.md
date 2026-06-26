# FAQ — AgentForge

---

### 1. Why LangGraph over AutoGen?

LangGraph provides explicit directed-graph control flow (not black-box agent loops), state persistence across nodes, conditional branching for review gates, built-in human-in-the-loop interrupts, and replay/debugging of any historical run. AutoGen is more flexible for free-form agent conversations but harder to audit and does not natively support the structured handoff pattern AgentForge requires. See [ADR-001](DECISIONS.md#adr-001-langgraph-over-autogen--crewai).

### 2. How do I add a new model to the registry?

1. Add an entry to `apps/api/core/model_registry.py` with all fields (id, provider, context window, cost, max output, timeout)
2. Add the API key environment variable in `apps/api/core/config.py` (if new provider)
3. Add a fallback chain in `apps/api/agents/providers.py`
4. Update `docs/MODEL_REGISTRY.md` with the new model's details

### 3. What happens when an agent fails mid-task?

The system follows this retry logic:
1. The LangGraph node catches the exception and increments `state.retry_count`
2. If `retry_count < max_retries` (default: 3): the node is re-invoked with the previous output as additional context
3. If `retry_count >= max_retries`: the task status is set to "failed", a human escalation is created, and the error is logged in `state.errors`
4. The WebSocket sends a `task_error` event with the error details

### 4. How is AI API cost tracked and attributed per task?

Each `task_steps` row records `tokens_in`, `tokens_out`, and `cost` (computed as `(tokens_in × input_price + tokens_out × output_price) / 1000`). The task's `total_cost` is the sum of all step costs. Costs are recorded in USD with 6 decimal precision. The usage dashboard shows per-project, per-model, and per-task cost breakdowns.

### 5. Can two agents run in parallel in the same task?

**Not yet in v0.3.** The current LangGraph graph executes nodes sequentially. Parallel agent execution is planned for v1.5, pending LangGraph's branch-and-merge parallelism support. The architecture supports it — agent outputs are independent per role, and the state merge is well-defined.

### 6. How do I reset my local database?

```bash
# Drop and recreate the database
docker compose down
docker compose up -d
pnpm db:migrate
pnpm db:seed
```

Or use the reset command:
```bash
pnpm db:reset  # Drops, recreates, migrates, and seeds
```

### 7. How does the WebSocket reconnect after a dropped connection?

The WebSocket client in `apps/web/lib/ws-client.ts` implements exponential backoff:
1. On close, wait 1 second
2. If still disconnected, wait 2 seconds
3. Double the wait on each subsequent attempt (up to 30 seconds max)
4. On reconnect, re-authenticate by sending the JWT token
5. Missed events during disconnection are not replayed — the client must reload the task state via `GET /api/v1/tasks/{id}`

### 8. What is the difference between a Task and a Task Step in the schema?

A **Task** (`tasks` table) is the top-level work unit — it has a title, description, status, and cumulative cost/token counts. A **Task Step** (`task_steps` table) is one atomic execution within a task — each step represents one agent node invocation. A task with 6 agents executing sequentially will have 6 steps (or more if revision cycles occur). The step tracks the specific agent, model, tokens, cost, and confidence for that single execution.

### 9. How do I write and register a new agent role?

Follow the recipe in [CLAUDE.md](CLAUDE.md#add-a-new-agent-role):
1. Add role to `AgentRole` enum (TS) and CHECK constraint (Prisma)
2. Create system prompt template in `apps/api/agents/prompts/`
3. Create node implementation in `apps/api/agents/nodes/`
4. Register node in `apps/api/agents/graph.py`
5. Update `AGENT_ROLES.md` and `AGENT_PROMPTS.md`

### 10. Where does agent output get stored and how is it retrieved?

Agent output is stored in two places:
- **During execution:** The output is stored in the LangGraph `AgentState` (`state.agent_outputs[role]`) and published to Redis pub/sub for real-time WebSocket streaming
- **After completion:** The output is persisted to the `outputs` table (files) and `messages` table (text messages) in PostgreSQL
- **For long-term retrieval:** Task summaries are embedded and stored in `agent_memories` table (pgvector) for semantic search

To retrieve: `GET /api/v1/tasks/{id}/output` returns all files, `GET /api/v1/tasks/{id}` returns all steps with their outputs.

### 11. What is the human-in-the-loop model?

The human is not replaced — the human is elevated. The human's role shifts from writing code to managing an AI engineering team. The human: creates projects, assembles the team, writes task descriptions, monitors live execution, approves/rejects deliverables, and requests revisions. The AI agents do all implementation, review, testing, and audit work. See [PRD.md](PRD.md#human-in-the-loop-model).

### 12. How are API keys for AI providers secured?

AI provider API keys are:
- Stored encrypted at rest using AES-256 (the `ENCRYPTION_KEY` env var)
- Decrypted in memory only when a task is being executed
- Never logged to any log file or console
- Never sent to the frontend
- Never included in agent output or context

### 13. What happens if Redis goes down?

Agent execution continues normally — the LangGraph graph runs independently of Redis. However:
- WebSocket real-time streaming stops working (no pub/sub relay)
- JWT validation caching falls back to validating on every request
- Rate limiting is bypassed (no enforcement)
- Task results are still saved to PostgreSQL, so no data is lost

When Redis recovers, WebSocket streaming resumes (new connections will work).

### 14. How does the confidence score work?

After each agent step, the agent includes a `confidence` score (0.0–1.0) in its output. This is the model's self-assessment of its output correctness. The system enforces minimum confidence thresholds per role (0.6 for Team Lead/QA, 0.7 for Backend/Frontend/Security/DevOps). Below-threshold outputs trigger a retry. The confidence score is not a technical metric — it is a heuristic based on the model's own certainty. See [HALLUCINATION_GUARD.md](HALLUCINATION_GUARD.md#layer-2-confidence-score-system).

### 15. Can I use AgentForge for non-code tasks (documentation, planning, etc.)?

Yes. AgentForge is role-based, not code-specific. The Team Lead, Reviewer, and QA roles can handle documentation, architecture planning, requirements analysis, and other knowledge work. However, the system is optimized for code generation — the Backend Engineer, Frontend Engineer, and Security Engineer roles are designed for software development workflows. For pure documentation tasks, consider customizing the system prompts or disabling code-specific roles.
