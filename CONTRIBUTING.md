# Contributing Guide — AgentForge

Thank you for contributing to AgentForge! This guide outlines our development processes, branch strategies, formatting guidelines, and pull request procedures.

---

## 1. Branch Strategy

We organize development branches using a strict structure to keep commits clean:

```text
main (protected)
  └── develop (integration branch)
       ├── feat/*       (new features)
       ├── fix/*        (bug fixes)
       ├── chore/*      (maintenance, dependencies)
       ├── docs/*       (documentation updates)
       ├── refactor/*   (code structure optimization)
       └── test/*       (testing enhancements)
```

* `main` is protected. No direct commits. Releases are merged here from release branches.
* `develop` is the integration branch. All feature branches merge here via Pull Requests.
* Feature branches are created from `develop` and must merge back via squash-merge.

---

## 2. Commit Message & PR Format

We use **Conventional Commits**: `type(scope): description`

### Types
* `feat`: New user-facing feature (agent node, API endpoint, UI component).
* `fix`: Bug fix in code.
* `chore`: Dependency updates, tool configurations, build tasks.
* `docs`: Documentation updates.
* `refactor`: Restructuring code without changing behavior.
* `test`: Adding or adjusting test suites.

### Examples
* `feat(agents): integrate security_node for dependency validation`
* `fix(auth): resolve jwt token expiration check crash`
* `docs(api): update WebSocket event schemas in API_REFERENCE.md`

---

## 3. Pull Request Process

### Step 1: Create a PR
Submit a PR from your feature branch to the `develop` branch. Ensure the title follows conventional formats.

### Step 2: Use the PR Template
All PR descriptions must complete the checklist:
```markdown
## Summary
<!-- Describe the change and the rationale -->

## Changes
<!-- List file paths modified -->
- `apps/api/agents/nodes/reviewer_node.py`

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
```

### Step 3: Required Checklists & Approvals
Before merging, a PR must meet these criteria:
* **Linting:** Python (`ruff check`), TypeScript (`pnpm run lint`) must pass.
* **Typing:** TypeScript checking (`tsc --noEmit`) must succeed.
* **Testing:** All unit tests pass.
* **Approvals:** At least one peer review approval.

---

## 4. Code Review Guidelines

Reviewers and authors should verify the following architectural layers:

### Agent Nodes
* Check that system templates are maintained in [docs/agents/AGENT_SYSTEM.md](file:///c:/Users/garvi/AgentForge/docs/agents/AGENT_SYSTEM.md).
* Node functions must match the signature `async def node_name(state: AgentState) -> AgentState`.
* Timeout and model parameters must resolve using `settings.agent_timeout.get("agent_name", default)` rather than direct dictionary brackets.

### API & Database
* Validate that schema changes are written as raw SQL migrations under `apps/api/migrations/` (no ORM schema files).
* Ensure Pydantic request and response schemas are specified for all new route functions in [docs/api/API_REFERENCE.md](file:///c:/Users/garvi/AgentForge/docs/api/API_REFERENCE.md).

### Frontend
* Verify React component props are typed.
* Handle loading, empty, and HTTP error states with beautiful visual feedback.
