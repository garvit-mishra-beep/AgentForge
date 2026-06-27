# `docs/api/`

Public API reference. Anything a third-party client (CLI, mobile, partner) needs
to integrate with AgentForge.

## Contents

| Doc | Purpose |
|-----|---------|
| [`API.md`](./API.md) | Complete REST + WebSocket reference — routes, payloads, error codes, auth |

## Architecture

```mermaid
graph LR
  Client[Web / CLI / Third-party] --> Auth[JWT Bearer]
  Auth --> REST[/api/v1/* REST endpoints/]
  REST --> DB[(PostgreSQL)]
  REST --> Redis[(Redis)]
  Client -. WebSocket .-> WS[/ws/* (planned)/]
```

## Responsibilities

- Document every public endpoint, including request/response schemas.
- Capture error codes and rate-limit headers.
- Be the **only** place where external clients should learn about the contract —
  no behavior is "discoverable from the code, undocumented here."

## Do Not Place Here

- Internal implementation details (e.g. graph traversal, node ordering) — those
  belong in `docs/architecture/SYSTEM_ARCHITECTURE.md`.
- Auth policy rationale (why JWT vs session) — `docs/security/SECURITY_MODEL.md`.
- Operator dashboards or admin endpoints — `docs/deployment/`.

## Related Modules

- Implementation: `apps/api/app/routes/`.
- Schemas: `apps/api/models/schemas.py`.
- Tests: `apps/api/tests/test_*.py` show example requests/responses.