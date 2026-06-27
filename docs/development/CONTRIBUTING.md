# Contributing Guide — AgentForge

**Last Updated:** June 2026

---

## Branch Strategy

```
main (protected)
  └── develop (integration branch)
       ├── feat/*       (new features)
       ├── fix/*        (bug fixes)
       ├── chore/*      (maintenance, deps)
       ├── docs/*       (documentation)
       ├── refactor/*   (code restructuring)
       └── test/*       (testing additions)
```

- `main` is protected — no direct pushes. All changes via PR.
- `develop` is the integration branch. PRs merge into `develop`.
- Feature branches branch off `develop` and merge back.
- Release branches (`release/v*`) branch off `develop` and merge to `main` + `develop`.

---

## PR Process

### 1. Create a PR

Title format: `type(scope): brief description`

Examples:
- `feat(agent): add security engineer role with audit node`
- `fix(ws): add ping/pong keepalive to WebSocket connections`
- `chore(deps): upgrade langgraph to 0.2.15`
- `docs(schema): add agent_memories table definition`

### 2. Fill PR Template

```markdown
## Summary
<!-- 1-3 sentences describing the change and why it's needed -->

## Changes
<!-- List of specific changes with file paths -->
- `apps/api/agents/nodes/security_node.py` — new security audit node
- `apps/api/agents/prompts/security.jinja2` — system prompt template
- `apps/api/agents/graph.py` — registered security node and conditional edges

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing steps performed

## Screenshots (if UI change)
<!-- Attach screenshots or screen recordings -->

## Related Issues
Closes #123
```

### 3. Required Checks

- [ ] Lint passes (ESLint + Prettier + Ruff)
- [ ] TypeScript type check passes (`tsc --noEmit`)
- [ ] Unit tests pass (`pnpm test:web && pnpm test:api`)
- [ ] Integration tests pass
- [ ] No new warnings

### 4. Required Approvals

- 1 approval from a team member
- For agent/prompt changes: 1 approval from Docs lead (for AGENT_PROMPTS.md update)
- For schema changes: 1 approval from Backend lead

### 5. Merge

- Squash merge into `develop` (keeps history clean)
- Merge commit into `main` for releases

---

## Commit Format (Conventional Commits)

```
type(scope): description

[optional body]
```

### Types

| Type | When to use |
|------|------------|
| `feat` | New feature for the user (agent role, API endpoint, UI component) |
| `fix` | Bug fix |
| `chore` | Maintenance, dependency updates, tooling |
| `docs` | Documentation changes |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration changes |

### Examples from AgentForge

```
feat(agents): add security engineer role with OWASP audit node

Implements the Security Engineer agent role that reviews code for
JWT vulnerabilities, SQL injection, XSS, and secrets exposure.

fix(ws): add ping/pong keepalive to prevent silent disconnect

WebSocket now sends a ping frame every 30 seconds. Connections that
don't respond within 10 seconds are closed and the frontend reconnects.

chore(deps): upgrade langgraph from 0.2.10 to 0.2.15

Fixes a conditional edge routing bug in subgraph execution.

docs(schema): add agent_memories table with pgvector index

docs(api): add WebSocket event types reference table

test(agents): add unit tests for backend_implement node

Covers: happy path, empty response, API failure, schema validation error.
Current coverage: 85%.
```

---

## Code Review Checklist

For every PR, the reviewer checks:

### General
- [ ] Code follows conventions in CONVENTIONS.md
- [ ] No hardcoded values that should be configuration
- [ ] No commented-out code
- [ ] Error handling present for all failure modes
- [ ] Logging at appropriate level (not too verbose, not silent)

### Agent Changes
- [ ] Prompt templates are versioned (v1.0, v1.1, etc.)
- [ ] System prompt template includes all required injectable variables
- [ ] Node function follows the `(state: AgentState) -> AgentState` signature
- [ ] Node is registered in `graph.py` with correct edges
- [ ] Output validation present (schema check)
- [ ] AGENT_ROLES.md and AGENT_PROMPTS.md updated

### API Changes
- [ ] Pydantic schemas defined for request/response
- [ ] Auth dependency (`get_current_user`) applied
- [ ] Proper HTTP status codes used (201 for create, 204 for delete, etc.)
- [ ] Error responses are structured (not raw exceptions)
- [ ] API.md documentation updated

### Schema Changes
- [ ] Prisma schema updated
- [ ] Migration generated and reviewed
- [ ] SCHEMA.md updated
- [ ] Migration is reversible

### Frontend Changes
- [ ] `"use client"` directive included for interactive components
- [ ] TypeScript interfaces for all props
- [ ] Loading, empty, and error states handled
- [ ] Responsive layout (mobile-first)
- [ ] WebSocket events documented in ws-client.ts

### Testing
- [ ] Unit tests cover new code (minimum 80% coverage)
- [ ] Integration tests if applicable
- [ ] E2E tests if UI change

---

## Bug Report Template

```markdown
## Bug Description
<!-- Clear, concise description -->

## Reproduction Steps
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Environment
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v0.3.0]

## Screenshots
<!-- If applicable -->

## Additional Context
<!-- Logs, error messages, etc. -->
```

---

## Feature Request Template

```markdown
## Problem Statement
<!-- What problem does this feature solve? -->

## Proposed Solution
<!-- How should this feature work? -->

## Alternative Solutions
<!-- What else did you consider? -->

## Acceptance Criteria
<!-- How will we know this feature is done? -->
- [ ] Criterion 1
- [ ] Criterion 2
```
