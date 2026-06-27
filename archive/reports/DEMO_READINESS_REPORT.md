# Demo Readiness Report

**Date:** 2026-06-26
**Auditor:** Principal QA Engineer
**Scope:** Frontend demo flow — team creation, task execution, execution viewing, navigation

---

## Demo Readiness Score: **2/10**

The self-contained `/demo` page works in isolation, but every real backend interaction will fail during a live demo. Creating a team, running a task, and viewing an execution all break at the API contract level.

---

## Top 10 Issues (by fix order)

---

### 1. P0 — Executions list links to wrong route (apps/web/app/executions/page.tsx:85)

```
<Link href={`/tasks/${exec.task_id}`}>
```

Every row in the executions list links to `/tasks/[task_id]`. The `/executions/[id]` route exists but is **unreachable from normal navigation**. You must type the URL manually. Fix: link to `/executions/${exec.id}` instead, which requires fixing issue 2 first.

---

### 2. P0 — /executions/[id] passes wrong ID type to every API call (apps/web/app/executions/[id]/page.tsx:94-97)

```
const { id } = use(params); // id is an execution ID
getTask(id);                // expects task ID — 404
getTaskMessages(id);        // expects task ID — 404
getExecution(id);           // backend route: GET /executions/{task_id} — 404
```

The URL param is an execution ID, but all three API functions expect a task ID. An execution's `id` and `task_id` are different UUIDs. Every API call returns 404, and the page always renders "Execution not found." The page must first resolve the execution to get `task_id`, then use that for task/message lookups. Requires a new `getExecutionById()` API function (or inline fetch).

---

### 3. P0 — Backend AgentRole enum has no tester role (apps/api/models/schemas.py:7-10)

```python
class AgentRole(str, Enum):
    team_lead = "team_lead"
    builder = "builder"
    reviewer = "reviewer"
    # tester is MISSING
```

The frontend defines 4 roles (team_lead, builder, reviewer, tester) but the backend schema only accepts 3. Adding a tester via the Team Builder fails with HTTP 422. The 5-step pipeline (Plan -> Build -> Review -> Test -> Deliver) depends on tester. Fix: add `tester = "tester"` to the backend AgentRole enum.

---

### 4. P0 — API client has no request timeout (apps/web/lib/api.ts:5-19)

```ts
const res = await fetch(`${BASE}${path}`, { ... });
```

No `AbortController`/`AbortSignal`. If the backend is down, the UI hangs for 60-300 seconds with spinning loaders. Fix: add a 10-second timeout using AbortController.

---

### 5. P0 — createTask sends project_id that backend rejects (apps/web/lib/api.ts:67-69)

```ts
createTask(data: { team_id, title, description, project_id? })
```

The backend TaskCreate schema has only `team_id`, `title`, `description` (no `project_id`). FastAPI/pydantic rejects unknown fields with 422 by default. Creating any task fails. Fix: strip `project_id` from the API call or add it to the backend schema.

---

### 6. P0 — updateTeam uses PATCH, backend only accepts PUT (apps/web/lib/api.ts:34-35) (apps/api/app/routes/teams.py:63)

Frontend sends `PATCH /teams/{id}`, backend has `@router.put("/{team_id}")`. HTTP 405 on every call. Fix: align method (change frontend to PUT or backend to PATCH).

---

### 7. P0 — updateTeamMember endpoint does not exist on backend (apps/web/lib/api.ts:46-48)

Frontend calls `PATCH /teams/{teamId}/members/{memberId}`. No such route exists on the backend. HTTP 404 on every call. Fix: remove the frontend call or add a backend route.

---

### 8. P1 — Inconsistent "ready team" thresholds (2 vs 3 members)

- apps/web/app/teams/page.tsx:181 — "Ready" badge at >= 3 members
- apps/web/app/tasks/page.tsx:94 — team selector shows teams with >= 2 members
- apps/web/app/teams/[id]/page.tsx — "Create Task" button enabled at >= 3 members

A team with exactly 2 members appears selectable in the task creation form but is marked incomplete everywhere else. Fix: unify to >= 3 members everywhere.

---

### 9. P1 — No error.tsx at any route level

No route-level `error.tsx` exists anywhere in the app. All errors fall through to the root ErrorBoundary, which shows a generic "Something went wrong" with no retry context. Fix: add `error.tsx` at `/teams`, `/tasks`, `/executions` route segments.

---

### 10. P1 — Templates only pre-fill team name, not members (apps/web/app/teams/page.tsx:115-136)

Template cards show 3-4 member roles with badges, but clicking a template only calls `setName(template.name)`. The member configurations are ignored. Users expect templates to auto-configure the team. Fix: populate team members when a template is selected, or remove role badges from template cards.

---

## Fix Order (recommended execution sequence)

| Order | Issue | Effort | Why this order |
|-------|-------|--------|----------------|
| 1 | #3 — Add tester to backend AgentRole enum | 5 min | Unblocks team creation and execution pipeline |
| 2 | #5 — Strip project_id from createTask | 5 min | Unblocks task creation |
| 3 | #6 — Align updateTeam method (PUT vs PATCH) | 2 min | Removes silent 405 |
| 4 | #7 — Remove or stub updateTeamMember | 2 min | Removes silent 404 |
| 5 | #4 — Add AbortController timeout to API client | 10 min | Prevents UI freeze on backend down |
| 6 | #2 — Fix /executions/[id] ID routing | 30 min | Makes execution detail page functional |
| 7 | #1 — Fix executions list links | 2 min | Makes execution detail page reachable |
| 8 | #8 — Unify ready team thresholds | 5 min | Fixes inconsistent UX |
| 9 | #9 — Add error.tsx files | 15 min | Route-level error recovery |
| 10 | #10 — Fix template system | 15 min | Template expectations match reality |

---

## Summary

| Metric | Value |
|--------|-------|
| Routes that render without crash | 12/12 |
| Routes that complete a full user flow | 2/12 |
| P0 issues | 7 |
| P1 issues | 3 |
| Estimated total fix time | ~1.5 hours |
| Demo readiness | Not ready |

12 routes minus `/demo` (fully self-contained). All 11 API-dependent routes break when the backend is running because of schema mismatches between frontend types and backend models.
