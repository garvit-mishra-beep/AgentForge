# Known Bugs — AgentForge

**Last Updated:** June 2026

---

## P0 — Critical

### P0-001: Agent hangs on LangGraph cycle with no timeout enforcement

**Severity:** Critical
**Status:** Fix in progress

**Description:** When a LangGraph conditional edge routes back to a previous node (e.g., review → backend revision), there is no limit on how many times this cycle can repeat. If the review always finds issues, the cycle continues indefinitely. The task never completes.

**Reproduction Steps:**
1. Create a task and assign it to a team
2. Configure the Reviewer to always find blocking issues
3. The Backend Engineer → Reviewer cycle repeats without termination

**Workaround:** Monitor running tasks. Kill stuck tasks via admin API.

**Assigned to:** Backend team

**Fix:** Enforce `MAX_STEPS=20` in the orchestrator. After 20 steps, force-terminate the task and expose it to the human.

---

### P0-002: WebSocket silently drops after 5 minutes idle

**Severity:** Critical
**Status:** Fix in progress

**Description:** WebSocket connections that remain idle for 5 minutes are silently closed by the infrastructure (load balancer, proxy, or browser). The frontend does not detect this until the next attempted send. Users think the connection is still alive but receive no updates.

**Reproduction Steps:**
1. Open a task view and watch agent execution
2. Wait 5 minutes without any agent activity (e.g., human-in-the-loop interrupt)
3. When the agent resumes, no updates appear in the browser

**Workaround:** Refresh the page to reconnect.

**Assigned to:** Frontend team

**Fix:** Implement ping/pong keepalive (30s interval). Frontend: detect silent close via a heartbeat timeout and auto-reconnect.

---

### P0-003: Task output not persisted when agent errors mid-step

**Severity:** Critical
**Status:** Fix in progress

**Description:** If an agent node raises an exception mid-execution (after writing some state updates but before completing), the partial output is lost. The task_steps row is created but the output and messages are empty.

**Reproduction Steps:**
1. Configure an agent to raise an exception after writing output
2. Create a task
3. Check task_steps table — the failed step has no output data

**Workaround:** None. The task must be re-created.

**Assigned to:** Backend team

**Fix:** Wrap each LangGraph node in a try/finally block that persists any partial output before re-raising the error. The WebSocket should also send a `task_error` event before closing.

---

## P1 — High

### P1-004: Role assignment UI broken for teams with >4 members

**Severity:** High
**Status:** Triaged

**Description:** The drag-and-drop role assignment grid in the Team Builder page overflows its container when 5+ agents are added. The grid wraps in an unpredictable layout that makes it impossible to assign roles.

**Reproduction Steps:**
1. Go to Team Builder
2. Add 5+ agents to the team
3. The grid layout breaks — agents overlap or extend beyond the container

**Workaround:** Use the API directly (`POST /api/v1/teams/{id}/agents`) for teams with >4 members.

**Assigned to:** Frontend team

---

### P1-005: Redis TTL not set on JWT validation cache keys

**Severity:** High
**Status:** Unassigned

**Description:** The JWT validation cache stores tokens in Redis without an expiry (TTL). Over time, this causes Redis memory to grow unboundedly, eventually triggering OOM evictions.

**Reproduction Steps:**
1. Make 10,000 API requests with different JWT tokens
2. Check Redis memory: `redis-cli INFO memory`
3. All 10,000 cache entries are still present

**Workaround:** None. Restart Redis to clear cache.

**Assigned to:** Unassigned

**Fix:** Add `redis.setex(key, 3600, ...)` (1 hour TTL) when storing JWT cache entries.

---

### P1-006: Model selector does not validate API key before saving

**Severity:** High
**Status:** Unassigned

**Description:** When a user selects a model in the Team Builder, the system saves the assignment without checking if the corresponding API key is configured and valid. At execution time, the task fails with an API key error.

**Reproduction Steps:**
1. Create a team with Qwen-72B assigned to QA role
2. Do NOT set `ALIBABA_API_KEY` in environment
3. Create a task — the QA step fails with "API key not configured"

**Workaround:** Ensure all API keys for selected models are configured before running tasks.

**Assigned to:** Backend team

**Fix:** On model assignment, validate that the model's provider API key is configured and responds to a test request. Show a validation error in the UI.

---

### P1-007: Dark mode flash on page reload

**Severity:** High
**Status:** Unassigned

**Description:** On page reload, the UI briefly flashes in light mode before switching to dark mode (when dark mode is the user's preference). This causes a jarring visual flicker.

**Reproduction Steps:**
1. Set dark mode preference (system or manual)
2. Reload any page
3. Observe light mode flash for ~200ms before dark mode activates

**Workaround:** None. Visual discomfort only, no functional impact.

**Assigned to:** Frontend team

**Fix:** Add `next-themes` SSR configuration with a `<script>` tag in `_document.tsx` that sets the dark class before React hydration.

---

## P2 — Medium

### P2-008: Copy button non-functional in output panel

**Severity:** Medium
**Status:** Unassigned

**Description:** The "Copy" button in the output panel's code block header does not copy the code to the clipboard. Clicking the button shows a brief visual feedback ("Copied!") but nothing is actually copied.

**Reproduction Steps:**
1. Open a completed task
2. Click the "Copy" button on any code block in the output panel
3. Paste into a text editor — nothing appears

**Workaround:** Manually select the code and copy with Ctrl+C.

**Assigned to:** Frontend team

---

### P2-009: Mobile layout broken on task detail view

**Severity:** Medium
**Status:** Unassigned

**Description:** The task detail view has a side-by-side layout (agent conversation panel + output panel). On screens narrower than 1024px, the flex container overflows horizontally and panels overlap.

**Reproduction Steps:**
1. Open a task detail view
2. Resize the browser to < 1024px width
3. The layout breaks — panels overlap and overflow

**Workaround:** Use a desktop-width browser.

**Assigned to:** Frontend team

---

### P2-010: Slow query on task history page

**Severity:** Medium
**Status:** Unassigned

**Description:** The task history page query becomes slow (>5 seconds) when there are more than 1000 tasks in a project. The query does a full table scan because it's missing a composite index on `(project_id, created_at)`.

**Reproduction Steps:**
1. Create 1000+ tasks in a single project
2. Navigate to the History page
3. The page takes 5-10 seconds to load

**Workaround:** None. Only affects projects with many tasks.

**Assigned to:** Backend team

**Fix:** Add composite index: `CREATE INDEX idx_tasks_project_created ON tasks (project_id, created_at DESC);`
