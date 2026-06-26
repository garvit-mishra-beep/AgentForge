# Agent Roles — AgentForge

**Last Updated:** June 2026 | **Prompt Version:** v1.0

---

## Overview

AgentForge defines 6 agent roles, each mapping to a real software engineering job function. Each role has a specific responsibility, system prompt template, output format, failure behavior, and handoff protocol.

---

## 1. Team Lead

**Recommended Model:** Gemini 1.5 Pro

### Responsibilities

- Analyze raw task descriptions and codebase context
- Break down tasks into structured subtask plans
- Identify unknowns, risks, and dependencies
- Create acceptance criteria for each subtask
- Review final agent outputs against original requirements
- Write a human-readable delivery summary
- Escalate to human when agents fail or blocked issues surface

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{task}` | User input | Raw task description |
| `{codebase_summary}` | Project scan | Language, frameworks, file tree, key modules |
| `{agent_outputs}` | All prior agents | Aggregated outputs from backend, reviewer, QA, security |
| `{acceptance_criteria}` | Generated in plan step | Criteria the final output must meet |

### Expected Output Format

```json
{
  "plan": [
    {
      "step": 1,
      "role": "backend",
      "description": "Implement JWT auth service",
      "files": ["app/services/auth.py", "app/routes/auth.py"],
      "acceptance_criteria": ["POST /auth/login returns token", "Token expires after configured TTL"]
    }
  ],
  "risks": ["Rate limiting not yet implemented"],
  "unknowns": ["Which hashing algorithm for passwords?"]
}
```

### Failure Behavior

| Failure | Action |
|---------|--------|
| Plan is empty or malformed | Retry (max 2) |
| Plan references non-existent files | Retry with corrected context |
| Confidence < 0.6 | Escalate to human |

### Handoff Protocol

- **To:** Backend Engineer — passes `plan` (subtask list with acceptance criteria)
- **From:** All agents — receives aggregated outputs for final delivery
- **Data passed:** `{ plan, acceptance_criteria, agent_outputs }`

---

## 2. Backend Engineer

**Recommended Model:** Claude Sonnet 4.6

### Responsibilities

- Implement API endpoints with FastAPI
- Write database migrations and queries
- Design and implement service layer logic
- Handle authentication, authorization, and middleware
- Write inline comments and type hints
- Apply review feedback from Reviewer
- Fix failing tests from QA Engineer

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{task}` | User input or plan | Subtask description |
| `{codebase_summary}` | Project scan | Existing code structure, conventions |
| `{file_contents}` | Relevant files | Contents of files to be modified |
| `{acceptance_criteria}` | Team Lead plan | What the implementation must satisfy |
| `{review_feedback}` | Reviewer | Optional — feedback from review step |

### Expected Output Format

```json
{
  "files": [
    {
      "path": "app/services/auth.py",
      "content": "from datetime import timedelta\n...",
      "language": "python"
    }
  ],
  "summary": "Implemented JWT auth service with /auth/login and /auth/refresh endpoints.",
  "test_notes": ["Requires secrets table migration"]
}
```

### Failure Behavior

| Failure | Action |
|---------|--------|
| AI provider timeout | Retry with backoff (max 3, exponential) |
| Generated code has syntax errors | Retry with error message in context |
| Acceptance criteria not met | Retry with unmet criteria highlighted |
| Confidence < 0.7 | Escalate to human |

### Handoff Protocol

- **To:** Reviewer — passes `files`, `summary`, `test_notes`
- **From:** Team Lead — receives `plan` and `acceptance_criteria`
- **From:** Reviewer — receives `review_feedback` for revision cycles

---

## 3. Frontend Engineer

**Recommended Model:** GPT-4o

### Responsibilities

- Build React components with Next.js 15 App Router
- Implement UI state management (useReducer + Context)
- Connect frontend to backend API
- Design responsive layouts with Tailwind CSS
- Implement real-time WebSocket updates
- Handle loading, empty, and error states

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{task}` | User input or plan | UI task description |
| `{codebase_summary}` | Project scan | Component tree, existing pages, API client |
| `{api_schema}` | API | Available endpoints and their request/response shapes |
| `{design_notes}` | Plan | UX requirements |

### Expected Output Format

```json
{
  "files": [
    {
      "path": "components/features/AuthForm.tsx",
      "content": "\"use client\";\nimport ...",
      "language": "tsx"
    }
  ],
  "dependencies": ["shadcn input component", "lucide-react icons"],
  "api_changes_required": []
}
```

### Failure Behavior

| Failure | Action |
|---------|--------|
| Component has JSX errors | Retry with error message |
| Missing API client integration | Retry with API schema reminder |
| Confidence < 0.7 | Escalate |

### Handoff Protocol

- **To:** Reviewer (or Qa, depending on workflow)
- **From:** Team Lead — receives subtask description

---

## 4. QA Engineer

**Recommended Model:** Qwen-72B-Instruct

### Responsibilities

- Read implementation code and understand expected behavior
- Generate unit tests for all functions and endpoints
- Generate integration tests for full user flows
- Run tests and report results (pass/fail/error counts)
- Identify edge cases not covered by existing tests
- Validate acceptance criteria with test assertions

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{implementation}` | Backend/Frontend output | Code to test |
| `{acceptance_criteria}` | Team Lead plan | What the output should satisfy |
| `{existing_tests}` | Codebase | Existing test patterns |

### Expected Output Format

```json
{
  "test_files": [
    {
      "path": "tests/test_auth.py",
      "content": "import pytest\n...",
      "language": "python"
    }
  ],
  "test_results": {
    "passed": 12,
    "failed": 0,
    "errors": 0,
    "coverage_estimate": "85%"
  },
  "issues_found": [
    {
      "severity": "medium",
      "description": "No test for token refresh with expired refresh token",
      "file": "app/services/auth.py",
      "line": 45
    }
  ]
}
```

### Failure Behavior

| Failure | Action |
|---------|--------|
| Test file has syntax errors | Retry with error fix |
| All tests pass but code has no assertions | Retry with assertion requirement |
| Confidence < 0.6 | Escalate to human |

### Handoff Protocol

- **To:** Backend Engineer (if tests fail) or Security Engineer (if tests pass)
- **From:** Backend Engineer — receives implementation code

---

## 5. Security Engineer

**Recommended Model:** GPT-4o

### Responsibilities

- Review all code for security vulnerabilities
- Audit authentication flows (JWT signing, expiry, rotation)
- Check for SQL injection, XSS, CSRF, SSRF patterns
- Validate API key and secret handling
- Review RBAC implementation
- Generate structured security findings report

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{implementation}` | Backend/Frontend code | Full implementation |
| `{test_report}` | QA Engineer | Test results for context |
| `{security_policy}` | Config | Org-specific security rules |

### Expected Output Format

```json
{
  "findings": [
    {
      "severity": "critical",
      "title": "JWT secret hardcoded in source",
      "file": "app/services/auth.py",
      "line": 3,
      "description": "JWT secret key is hardcoded instead of read from environment variable"
    }
  ],
  "summary": "1 critical, 2 high, 1 medium, 0 low",
  "verdict": "blocked",
  "blocking_issues": ["JWT secret hardcoded"]
}
```

### Failure Behavior

| Failure | Action |
|--------|--------|
| Confidence < 0.7 | Retry with expanded security context |
| No findings found but critical patterns present | Retry with explicit pattern hints |
| Critical finding detected | Block delivery, always escalate to human |

### Handoff Protocol

- **To:** Team Lead (for delivery) or END (if critical findings block)
- **From:** QA Engineer — receives implementation + test report

---

## 6. DevOps Engineer

**Recommended Model:** Claude Haiku 4.5

### Responsibilities

- Generate Dockerfile and Docker Compose configurations
- Write GitHub Actions workflow files
- Create deployment configuration (Vercel, Railway)
- Set up CI/CD pipeline definitions
- Generate infrastructure-as-code files
- Document deployment procedures

### System Prompt Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{task}` | User input | DevOps task description |
| `{codebase_summary}` | Project scan | App structure, dependencies |
| `{infra_context}` | Config | Current deployment setup |

### Expected Output Format

```json
{
  "files": [
    {
      "path": "Dockerfile",
      "content": "FROM python:3.11-slim\n...",
      "language": "dockerfile"
    }
  ],
  "commands": ["docker build -t agentforge-api ."],
  "notes": ["Requires RAILWAY_ENVIRONMENT variable set in Railway dashboard"]
}
```

### Failure Behavior

| Failure | Action |
|---------|--------|
| Dockerfile has syntax errors | Retry with error message |
| Missing ENTRYPOINT or CMD | Retry with reminder |
| Confidence < 0.7 | Escalate |

### Handoff Protocol

- **To:** Team Lead (final review)
- **From:** Team Lead — receives task requirements
