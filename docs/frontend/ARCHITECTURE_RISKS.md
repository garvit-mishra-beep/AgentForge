# Architecture Risks

Risk register for frontend development, derived from backend audit.

---

## 🔴 P0 — Critical

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **No WebSocket support** | Backend has no WS endpoints. `ws-client.ts` is dead code. Task/execution pages must poll. | Polling fallback at 500-600ms intervals. Accept stale-data risk. |
| 2 | **No human-in-the-loop approval** | `POST /tasks/{id}/revise` does not exist. Approve/Revise UI buttons cannot function. | Logged in BACKEND_GAPS.md. Disable buttons with "coming soon" tooltip. |
| 3 | **Parallel 401 race condition** | Multiple simultaneous API calls hitting 401 could trigger multiple `/auth/refresh` calls, causing logout loops. | Implement refresh-lock in api.ts: only one refresh at a time, queue pending requests. |

## 🟠 P1 — High

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **Review endpoints use DEMO_USER_ID fallback** | `POST /review` and `GET /review/{id}` accept `user_id: str | None = None` and fall back to a hardcoded demo UUID. If auth is enabled, user_id must be explicitly extracted. | Frontend must always pass the Bearer token; review routes should use `Depends(require_user)` consistently. |
| 2 | **Analytics queries not paginated** | `GET /analytics/models` and `GET /analytics/teams` return all results. At scale (1000s of execs) this may time out. | Add limit/offset params. Client-side: show top N with "load more". |
| 3 | **Memories/Analytics POST/PUT accept raw JSON** | `POST /memories`, `PUT /memories/{id}`, `POST /analytics/track` use `await request.json()` with no Pydantic validation — any malformed body causes 500. | Frontend must validate before sending. Logged in BACKEND_GAPS.md. |

## 🟡 P2 — Medium

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **No query filters on GET /tasks** | No `status`, `project_id`, `team_id`, or `sort` params. `limit` and `offset` only. Client must filter/sort in-memory. | Acceptable for <50 tasks. Plan for server-side when paginating >200. |
| 2 | **No query filter on GET /executions** | No `status` filter param. Only `limit` and `offset`. Dashboard cannot ask "running only". | Client-side filter after fetch. |
| 3 | **`TaskMessageResponse` has no `tokens` field** | Token count display shows 0 everywhere. | Hide token column in UI or log as gap. |
| 4 | **Execution routes require task_id** | `GET /executions/{task_id}` requires task_id but `/executions/[id]` page has exec_id. Need extra lookup. | Frontend must call `GET /executions/detail/{exec_id}` which handles this. |
| 5 | **No review history list endpoint** | `/review/history` has no backing route. No way to list past reviews per user. | Collect review_ids in localStorage or skip page. |
| 6 | **No GET /teams/templates** | `/templates` page shows team templates but there's no backend route to list them. | Hardcode templates client-side. |

## 🔵 P3 — Low

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **No waitlist endpoint** | Landing page waitlist form has no backend route. | Store emails in localStorage or connect to a third-party service. |
| 2 | **`github_enhanced` routes not imported** | 4 endpoints for enhanced GitHub features exist but are never registered in `main.py`. | Don't expose in UI. Log as inactive in docs. |
| 3 | **No tenant isolation on review/language detection** | `/review/language/detect` is completely unauthenticated — anyone can hit it. | Acceptable for a utility endpoint. No sensitive data exposed. |

---

## Risk Summary

| Severity | Count | Action Required |
|----------|-------|-----------------|
| 🔴 P0 | 3 | Must be addressed or deferred with documented reason |
| 🟠 P1 | 3 | High impact — prioritize in roadmap |
| 🟡 P2 | 6 | Plan for post-MVP |
| 🔵 P3 | 3 | Acceptable for launch |
| **Total** | **15** | |
