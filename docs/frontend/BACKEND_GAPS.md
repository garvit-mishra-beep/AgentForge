# Backend Gaps

All gaps discovered during Phase 0 audit that block or degrade frontend features.

---

## GAP: WebSocket Streaming (No endpoint exists)
| Field | Value |
|-------|-------|
| Missing feature | WebSocket endpoint for real-time task/execution streaming |
| Current state | No `app/ws/` directory exists. No WebSocket handler registered in `main.py` |
| UI blocked | Real-time agent message streaming in `/tasks/[id]` and `/executions/[id]` |
| Fallback | Polling `GET /tasks/{id}/messages` every 500-600ms |
| Priority | P0 |

## GAP: Human-in-the-Loop Approval (Missing route)
| Field | Value |
|-------|-------|
| Missing route | `POST /api/v1/tasks/{id}/revise` or similar |
| Required schema | `{ verdict: "approved" \| "rejected", comment?: string }` |
| UI blocked | Approve/Revise buttons in `/tasks/[id]` human-interrupt panel |
| Recommended impl | Add to `app/routes/executions.py` |
| Priority | P0 |

## GAP: Query Filters on GET /tasks (Missing params)
| Field | Value |
|-------|-------|
| Missing params | `status`, `project_id`, `team_id`, `sort` — only `limit` and `offset` exist |
| UI blocked | Task filter bar in `/tasks` page cannot filter by status or project server-side |
| Fallback | Client-side filtering after fetch (acceptable for <50 tasks) |
| Priority | P2 |

## GAP: Query Filter on GET /executions (Missing param)
| Field | Value |
|-------|-------|
| Missing param | `status` filter — only `limit` and `offset` exist |
| UI blocked | Dashboard cannot request "running executions only" |
| Fallback | Client-side filter after fetch |
| Priority | P2 |

## GAP: tokens field on TaskMessageResponse (Missing field)
| Field | Value |
|-------|-------|
| Missing field | `tokens: int` on `TaskMessageResponse` schema |
| Schema file | `models/schemas.py:149-157` |
| UI affected | Token count metric cards display 0 everywhere |
| Priority | P2 |

## GAP: Review History List (Missing route)
| Field | Value |
|-------|-------|
| Missing route | `GET /api/v1/review` — no way to list past reviews |
| UI blocked | `/review/history` page has no data source |
| Fallback | Store review_ids in localStorage; not reliable |
| Priority | P2 |

## GAP: Team Template List (Missing route)
| Field | Value |
|-------|-------|
| Missing route | `GET /api/v1/teams/templates` — templates must be hardcoded |
| UI blocked | `/templates` page shows pre-built teams but has no API source |
| Fallback | Hardcode 6 templates client-side in `lib/templates.ts` |
| Priority | P3 |
