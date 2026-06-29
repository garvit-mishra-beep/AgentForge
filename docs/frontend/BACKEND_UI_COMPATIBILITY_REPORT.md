# Backend-UI Compatibility Report

Per-page analysis of required routes vs. actual backend availability.

---

| Page | Required Routes | All Exist? | Gaps |
|------|----------------|------------|------|
| `/login` | POST /auth/login | ✅ | None |
| `/register` | POST /auth/register | ✅ | None |
| `/dashboard` | GET /tasks, GET /executions, GET /analytics/dashboard | ✅ | No `status` filter param on GET /tasks or GET /executions |
| `/teams` | GET /teams, POST /teams | ✅ | None |
| `/teams/[id]` | GET /teams/{id}, PUT /teams/{id}, DELETE /teams/{id}, POST /teams/{id}/members, PUT /teams/{id}/members/{mid}, DELETE /teams/{id}/members/{mid} | ✅ | None |
| `/tasks` | GET /tasks, POST /tasks | ✅ | No `status`, `project_id`, `team_id` query filter params |
| `/tasks/[id]` | GET /tasks/{id}, GET /tasks/{id}/messages, WS task_stream | ⚠️ Partial | **WebSocket missing** — must poll. **No POST /tasks/{id}/revise** — human-in-loop blocked |
| `/executions` | GET /executions | ✅ | No `status` filter param |
| `/executions/[id]` | GET /executions/detail/{id}, GET /executions/{task_id} | ✅ | Requires task_id from route — needs client-side lookup |
| `/projects` | GET /projects, POST /projects | ✅ | None |
| `/projects/[id]` | GET /projects/{id}, PUT /projects/{id}, DELETE /projects/{id}, POST /upload, GET /files, DELETE /files/{id}, GET /download/{id}, POST /teams, DELETE /teams/{tid} | ✅ | None |
| `/review` | POST /review, GET /review/{id}, GET /review/{id}/status | ✅ | None |
| `/review/history` | GET /review?user_id (no such endpoint) | ❌ | **No review history list endpoint** — must collect review IDs client-side |
| `/analytics` | GET /analytics/dashboard, GET /analytics/trends, GET /analytics/models, GET /analytics/teams | ✅ | None |
| `/settings` | GET /keys, POST /keys, PUT /keys/{id}, DELETE /keys/{id}, POST /keys/{id}/set-default | ✅ | None |
| `/settings/providers` | GET /keys/providers, POST /keys/validate, POST /keys, GET /keys, PUT /keys/{id}, DELETE /keys/{id} | ✅ | None |
| `/templates` | POST /teams/template | ✅ | No GET /teams/templates — templates must be hardcoded or created on demand |
| `/benchmark` | POST /tasks (with specific configs) | ✅ | No dedicated benchmark route |
| `/demo` | (uses mock data) | ✅ | No demo-specific backend routes needed |
| `/` (landing) | GET /health (status check), POST /auth/register (waitlist) | ✅ | No waitlist endpoint — would need backend route |

---

## Summary

| Metric | Count |
|--------|-------|
| Pages with full route coverage | 16 |
| Pages with gaps | 4 |
| Total gaps identified | 6 |

## Key Gaps

| Gap | Affected Page | Priority |
|-----|---------------|----------|
| No WebSocket endpoint | /tasks/[id], /executions/[id] | P0 |
| No POST /tasks/{id}/revise | /tasks/[id] (human-in-loop) | P0 |
| No query filters on GET /tasks | /tasks, /dashboard | P2 |
| No query filter on GET /executions | /executions, /dashboard | P2 |
| No review history list | /review/history | P2 |
| No waitlist endpoint | / (landing page) | P3 |
