# Testing Guide — AgentForge

**Last Updated:** June 2026

---

## Test Pyramid

```
        ╱╲
       ╱ E2E ╲
      ╱────────╲
     ╱Integration╲
    ╱──────────────╲
   ╱   Unit Tests    ╲
  ╱────────────────────╲
 ╱  80%+ code coverage  ╲
```

---

## Unit Tests

### Frontend (Vitest)

**Framework:** Vitest + @testing-library/react

**Location:** `apps/web/components/__tests__/`

**Run:**
```bash
pnpm test:web          # Single run
pnpm test:web --watch  # Watch mode
pnpm test:web --coverage  # With coverage
```

**What to test:**
- React components (render states: loading, empty, error, success)
- Utility functions (format-tokens, api-client helpers, ws-client)
- Hooks and context providers

**Example:**
```typescript
// components/__tests__/AgentMessage.test.tsx
import { render, screen } from "@testing-library/react";
import { AgentMessage } from "@/components/agents/AgentMessage";

describe("AgentMessage", () => {
  it("renders role badge", () => {
    render(<AgentMessage role="backend" model="claude-sonnet-4-6" content="Test" />);
    expect(screen.getByText("backend")).toBeInTheDocument();
  });

  it("renders code blocks with syntax highlighting", () => {
    const content = "```python\nprint('hello')\n```";
    render(<AgentMessage role="backend" model="claude-sonnet-4-6" content={content} />);
    expect(screen.getByText("print('hello')")).toBeInTheDocument();
  });
});
```

### Backend (Pytest)

**Framework:** pytest + pytest-asyncio + pytest-httpx

**Location:** `apps/api/tests/`

**Run:**
```bash
pnpm test:api                       # All backend tests
pnpm test:api -- -k test_auth       # Filter by test name
pnpm test:api -- --cov=app --cov-report=term-missing  # Coverage
```

**What to test:**
- FastAPI route handlers (status codes, response schemas, auth enforcement)
- LangGraph nodes (with mocked AI provider calls)
- Database queries (with test database)
- Validation logic (Pydantic schemas, custom validators)

**Example:**
```python
# tests/test_routes/test_tasks.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock auth dependency
        app.dependency_overrides[get_current_user] = lambda: {"id": "user_test"}

        response = await client.post("/api/v1/tasks", json={
            "project_id": "proj_test",
            "team_id": "team_test",
            "title": "Test Task",
            "description": "A test task",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["status"] == "pending"
```

### Agent Nodes

**Framework:** pytest + mocked AI providers

**Location:** `apps/api/tests/test_agents/`

**Mocking AI providers:**
```python
# tests/conftest.py
@pytest.fixture
def mock_openai():
    with patch("app.agents.providers.openai_client.chat.completions.create") as mock:
        mock.return_value = {
            "choices": [{"message": {"content": '{"plan": []}'}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }
        yield mock
```

---

## Integration Tests

**Framework:** pytest + test PostgreSQL database

**Location:** `apps/api/tests/test_integration/`

**Run:**
```bash
pnpm test:integration
```

**What to test:**
- Full task execution with mocked AI responses
- WebSocket connection lifecycle (connect, auth, receive events, disconnect)
- Database read/write operations end-to-end
- Redis pub/sub message flow

**Example — Full Agent Graph Test:**
```python
# tests/test_integration/test_full_task_execution.py
@pytest.mark.asyncio
async def test_full_task_execution(mock_all_ai_providers, test_db, test_redis):
    # Create project, team, agents
    project = await create_test_project()
    team = await create_test_team(project.id)

    # Create task
    task = await create_task(project.id, team.id, "Build JWT Auth")

    # Execute
    result = await execute_task(task.id)

    # Assert
    assert result.status == "completed"
    assert len(result.steps) == 5  # Plan → Implement → Review → QA → Deliver
    assert result.total_tokens > 0
    assert result.total_cost > 0
    assert len(result.outputs) > 0  # At least one file generated
```

---

## E2E Tests (Playwright)

**Framework:** @playwright/test

**Location:** `tests/e2e/`

**Run:**
```bash
# Requires dev servers running
pnpm test:e2e

# With UI mode
pnpm test:e2e --ui

# Specific test
pnpm test:e2e --grep "Team Builder"
```

**What to test:**
- Team Builder flow (create team, assign agents, save)
- Task execution flow (create task, watch agent streaming, approve)
- History page (filter, search, view task details)
- Authentication flow (sign in, sign out, protected routes)

**Example:**
```typescript
// tests/e2e/task-execution.spec.ts
import { test, expect } from "@playwright/test";

test("create task and watch agent execution", async ({ page }) => {
  // Sign in
  await page.goto("/sign-in");
  await page.fill("[name=email]", "test@agentforge.dev");
  await page.fill("[name=password]", "test-password");
  await page.click("button[type=submit]");

  // Navigate to a project
  await page.click("text=My Project");

  // Create a task
  await page.click("button:has-text('New Task')");
  await page.fill("[name=title]", "Build JWT Auth");
  await page.fill("[name=description]", "Implement JWT authentication");
  await page.click("button:has-text('Create')");

  // Watch agent execution
  await expect(page.locator("[data-testid=agent-stream]")).toBeVisible();
  await expect(page.locator("[data-testid=agent-message]").first()).toBeVisible({ timeout: 30000 });

  // Wait for completion
  await expect(page.locator("[data-testid=task-complete]")).toBeVisible({ timeout: 300000 });
});
```

---

## Mocking External APIs

### Frontend (MSW)

```typescript
// apps/web/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("http://localhost:8000/api/v1/projects", () => {
    return HttpResponse.json({ projects: [] });
  }),
];
```

### Backend (pytest-httpx)

```python
# tests/conftest.py
@pytest.fixture
def mock_http():
    with pytest_httpx.HTTPXMock() as httpx_mock:
        httpx_mock.add_response(
            url="https://api.openai.com/v1/chat/completions",
            json={
                "choices": [{"message": {"content": '{"files": []}'}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
        )
        yield httpx_mock
```

---

## Coverage Requirements

| Layer | Minimum Coverage | Required For |
|-------|----------------|-------------|
| Frontend components | 70% | All PRs |
| Frontend utilities | 80% | All PRs |
| Backend routes | 80% | All PRs |
| Backend services | 80% | All PRs |
| Agent orchestration | 90% | All PRs |
| LangGraph nodes | 90% | All PRs |
| Validation logic | 95% | All PRs |

---

## CI Pipeline Order

```
1. Lint (eslint + prettier + ruff)    → ~30s
2. Type check (tsc + mypy)            → ~45s
3. Unit tests (vitest + pytest)       → ~2min
4. Integration tests                   → ~3min
5. E2E tests (Playwright)             → ~5min
                                       ──────
                              Total:  ~11min
```

If any stage fails, subsequent stages are skipped and the PR is blocked.
