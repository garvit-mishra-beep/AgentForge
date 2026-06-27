# Reusable Prompts — AgentForge

**10 Claude Code prompts for common development tasks.**

---

## 1. Add a New Agent Role with System Prompt

```
You are adding a new agent role to AgentForge. The role is called "{role_name}" and
should handle {role_responsibilities}.

1. Add the role value to the `AgentRole` enum in `packages/types/index.ts`
2. Add a CHECK constraint value to the Prisma schema in `packages/db/schema.prisma`
3. Create a system prompt template at `apps/api/agents/prompts/{role_name}.jinja2`.
   The template must include injectable variables: {task}, {codebase_summary},
   {previous_step_output}, {acceptance_criteria}.
4. Create a node implementation at `apps/api/agents/nodes/{role_name}_node.py`
   following the conventions in `docs/CONVENTIONS.md` (async function, prompt
   rendering, AI provider call, output validation, state update).
5. Register the node in `apps/api/agents/graph.py` and add conditional edges.
6. Update `docs/AGENT_ROLES.md` and `docs/AGENT_PROMPTS.md` with the new role spec.

Run `pnpm test:api` after implementation to verify no regressions.
```

---

## 2. Add an API Endpoint with Pydantic Schema

```
Add a new REST API endpoint to AgentForge for {resource}.

1. Define request and response Pydantic models in `apps/api/models/schemas.py`
2. Create `apps/api/app/routes/{resource}.py` with:
   - A FastAPI APIRouter
   - Async route handlers with type-annotated parameters
   - Clerk JWT dependency via `get_current_user` from `core/auth.py`
   - Proper error responses using HTTPException
3. Register the router in `apps/api/app/main.py`
4. Add tests in `tests/test_routes/test_{resource}.py` using pytest and httpx
5. Update `docs/API.md` with the new endpoint reference

Use existing routes (projects.py, teams.py, tasks.py) as style reference.
```

---

## 3. Write a DB Migration

```
I need to modify the database schema for AgentForge.

Change description: {migration_description}

1. Update `packages/db/schema.prisma` with the model or field changes
2. Create a migration: `pnpm db:migrate --name {short_description}`
3. Verify the generated SQL in `packages/db/migrations/` is correct
4. Run `pnpm db:generate` to update the Prisma client
5. Update `docs/SCHEMA.md` with the new table/column definitions

The migration should be reversible — include both `CREATE` and `ALTER` statements
so we can roll back if needed.
```

---

## 4. Add a WebSocket Event Handler

```
Add a new WebSocket event type to AgentForge.

Event type: {event_type}
Payload schema: {payload_description}

1. Add the event type to the `WSEventType` enum in:
   - `packages/types/index.ts` (TypeScript)
   - `apps/api/models/schemas.py` (Python enum)
2. Add a handler in `apps/api/app/ws/task_stream.py` that:
   - Receives the event from the LangGraph node via Redis pub/sub
   - Formats the WS event envelope (type, task_id, agent_id, role, model, timestamp, payload)
   - Sends the JSON-serialized event to the WebSocket connection
3. Add client-side dispatch in `apps/web/lib/ws-client.ts`:
   - A typed event handler that switches on `event.type`
   - Update the React context/state accordingly
4. Document the event in `docs/API.md` WebSocket section
```

---

## 5. Generate Unit Tests for a FastAPI Service

```
Write comprehensive unit tests for `apps/api/{service_path}`.

Test file: `tests/test_{service_name}.py`

Requirements:
- Use pytest + pytest-asyncio for async tests
- Use pytest-httpx to mock external HTTP calls (AI provider APIs)
- Mock asyncpg database calls
- Cover:
  - Happy path (successful execution)
  - Edge cases (empty input, missing fields)
  - Error cases (API failure, timeout, invalid response)
  - Rate limiting behavior
  - Auth failures (invalid/expired JWT)
- Minimum 90% code coverage on the service module

Run `pnpm test:api` and report coverage results.
```

---

## 6. Debug a LangGraph Agent Graph

```
I need to debug the LangGraph agent execution graph in `apps/api/agents/graph.py`.

The issue: {issue_description}

Steps:
1. Enable LangSmith tracing locally:
   - Set `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` in `.env`
   - Verify traces appear at https://smith.langchain.com
2. Add logging to each node in `apps/api/agents/nodes/`:
   - Log state keys before and after node execution
   - Log which conditional edge was taken and why
3. Add a test that executes the full graph with mocked AI responses
   - Test file: `tests/test_agent_graph.py`
   - Mock all AI provider calls to return controlled outputs
   - Assert on: graph termination, correct node sequence, final state values
4. Check for common issues:
   - Missing state key access (AgentState TypedDict)
   - Conditional edge routing function returns invalid value
   - Human-in-the-loop interrupt blocks without resume path

Report findings and the fix applied.
```

---

## 7. Add a React Component with Tailwind

```
Add a new React component to AgentForge.

Component name: {ComponentName}
Location: `apps/web/components/{category}/{ComponentName}.tsx`
Props: {props_description}

Requirements:
- Client component (`"use client"` directive at top)
- TypeScript with explicit prop interface
- Tailwind CSS for styling (no CSS modules or styled-components)
- Follow existing component patterns in `apps/web/components/`
- Include loading state (skeleton) and empty state
- Use shadcn/ui primitives from `apps/web/components/ui/` where applicable
- Add a story/test file at `apps/web/components/__tests__/{ComponentName}.test.tsx`

Test with `pnpm test:web` to verify.
```

---

## 8. Write an E2E Test with Playwright

```
Write an end-to-end test for AgentForge using Playwright.

Test scenario: {scenario_description}
Test file: `tests/e2e/{test_name}.spec.ts`

Requirements:
- Use `@playwright/test` with TypeScript
- Test the full user flow, not isolated UI pieces
- Mock the WebSocket connection to simulate agent responses
- Use Playwright fixtures for authentication (Clerk test user)
- Assert on:
  - Page navigation and URL
  - UI element presence and state
  - WebSocket event handling and UI updates
  - Error state display

Run `pnpm test:e2e` to execute.
```

---

## 9. Add Redis Caching to an Endpoint

```
Add Redis caching to the `{endpoint_path}` endpoint in AgentForge.

Requirements:
1. Use the existing Redis client from `apps/api/core/redis.py`
2. Cache key format: `cache:{resource}:{id}:{user_id}`
3. Cache TTL: {ttl_seconds} seconds (configurable via `REDIS_{RESOURCE}_TTL` env var)
4. Implement cache-aside pattern:
   - Check Redis cache first
   - On cache miss: query database, serialize to JSON, store in Redis, return
   - On cache hit: deserialize JSON and return
5. Invalidate cache on write operations (POST, PATCH, DELETE) for the affected resource
6. Add tests for cache hit, cache miss, and cache invalidation scenarios
7. Update `docs/ENV.md` if new environment variables were added

Use the JWT validation cache in `core/auth.py` as a reference implementation.
```

---

## 10. Refactor a LangGraph Node

```
Refactor the {node_name} LangGraph node in `apps/api/agents/nodes/{node_name}_node.py`.

Current issues: {issues_description}

Refactoring requirements:
1. Split the node into smaller, testable helper functions:
   - `build_prompt(state)` — renders the system prompt from template
   - `call_model(prompt, state)` — calls the AI provider with retry logic
   - `validate_output(response)` — validates output structure and confidence
   - `update_state(state, parsed, tokens)` — returns updated state
2. Move any hardcoded strings to constants or the prompt template
3. Add proper error handling:
   - AI provider timeout → retry with backoff (max 3 attempts)
   - Invalid output format → reject with specific error message
   - Confidence below threshold → escalate to human
4. Update the corresponding test file to cover the refactored functions
5. Run `pnpm test:api` and verify all tests pass

The refactored node must maintain the same input/output contract (AgentState → AgentState).
```
