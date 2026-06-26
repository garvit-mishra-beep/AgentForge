# Benchmark Framework — AgentForge MVP Validation

---

## 1. Objective

Prove or disprove: **Multi-model collaboration produces better code than a single frontier model.**

This is the core hypothesis of AgentForge. If true, the product has a defensible thesis. If false, the product must pivot or die.

### Hypotheses

| Hypothesis | Statement | Test |
|-----------|-----------|------|
| **H1 (Primary)** | AgentForge teams produce functionally correct code at a higher rate than single models | Compare correctness pass rate across 60 tasks |
| **H2 (Security)** | AgentForge teams catch more security vulnerabilities | Compare security finding counts |
| **H3 (Quality)** | AgentForge teams produce more maintainable code | Compare lint scores, complexity metrics |
| **H4 (Robustness)** | AgentForge teams produce code with higher test pass rates | Compare test suite pass rates |
| **H0 (Null)** | No statistically significant difference exists between single-model and multi-team output | All metrics fail to reach p < 0.05 |

---

## 2. Experimental Design

### 2.1 Conditions

| Condition | Description | Model Assignment | Cost Budget |
|-----------|-------------|-----------------|-------------|
| **A — Single Frontier** | One model does everything: plans, codes, reviews, delivers | Claude Sonnet 4.6 (best-in-class coding) | 1 pass |
| **B — Single Cheapest** | One cheap model does everything | GPT-4o-mini | 1 pass |
| **C — AgentForge Team** | 3 agents: Team Lead plans, Builder codes, Reviewer reviews | TL: Gemini 1.5 Pro, BL: Claude Sonnet 4.6, RV: GPT-4o | 1 pass |
| **D — AgentForge Ablation** | 3 agents, all same model (Claude Sonnet) to isolate architecture effect | TL: Claude Sonnet, BL: Claude Sonnet, RV: Claude Sonnet | 1 pass |

**Primary comparison:** A vs C — does the recommended AgentForge team beat a single best-in-class model?
**Ablation:** A vs D — does the multi-agent architecture help even without model diversity?
**Cost control:** A vs C — if C wins despite higher cost, the architecture works.

### 2.2 Task Count

60 tasks × 4 conditions = **240 total benchmark runs**

| Category | Count | Description |
|----------|-------|-------------|
| Bug fixes | 20 | "Fix this bug: [description + code]" |
| Feature requests | 20 | "Add this feature: [description]" |
| Refactors | 20 | "Refactor this module: [description + code]" |

### 2.3 Randomization & Blinding

- Task order is randomized per condition
- Evaluator model receives outputs **blind** — no condition label
- Outputs are shuffled before evaluation
- Human spot-check on 20% of evaluations to calibrate judge model

---

## 3. Benchmark Dataset

### 3.1 Bug Fixes (20)

All bugs are in a standardized Python codebase repository (a FastAPI todo app ~500 LOC).

| ID | Bug Description | Severity | Expected Fix |
|----|----------------|----------|-------------|
| BF-01 | `GET /todos` returns 500 when database has no records | Crash | Handle empty result set |
| BF-02 | `POST /todos` accepts empty title, creates blank todo | Data | Add request validation |
| BF-03 | `DELETE /todos/{id}` returns 500 for non-existent ID | Crash | Check existence before delete |
| BF-04 | JWT token never expires (no expiry check) | Security | Add token expiry validation |
| BF-05 | Password stored in plaintext | Security | Add bcrypt hashing |
| BF-06 | Rate limiting not applied to login endpoint | Security | Add rate limit decorator |
| BF-07 | CORS configured as `*` in production | Security | Lock to specific origins |
| BF-08 | SQL injection in search endpoint (`SELECT ... WHERE title = '{input}'`) | Security | Parameterize query |
| BF-09 | Off-by-one error in pagination (page 2 misses first item) | Logic | Fix offset calculation |
| BF-10 | Race condition on concurrent todo status updates | Logic | Add row-level locking |
| BF-11 | Error message exposes internal path (`/app/venv/lib/...`) | UX | Sanitize error messages |
| BF-12 | Timeout not set on external API call (hangs indefinitely) | Reliability | Add httpx timeout |
| BF-13 | Logging outputs API keys in debug mode | Security | Add log sanitization |
| BF-14 | File upload accepts any file type (no extension validation) | Security | Add MIME type check |
| BF-15 | Email validation accepts `user@.com` as valid | Logic | Fix regex |
| BF-16 | Sort order parameter allows SQL injection-like characters | Security | Validate sort parameter |
| BF-17 | WebSocket connection not closed on task completion | Resource | Add cleanup handler |
| BF-18 | Database connection pool exhausted under load (no release) | Reliability | Fix connection release |
| BF-19 | Required `created_at` field allows NULL in DB insert | Data | Add default value |
| BF-20 | Health check endpoint calls database (failing when DB is down) | Design | Make health check stateless |

### 3.2 Feature Requests (20)

All features extend the same todo app codebase.

| ID | Feature Description | Complexity | Acceptance Criteria |
|----|-------------------|------------|-------------------|
| FR-01 | Add `PUT /todos/{id}` endpoint to update todo title/status | Easy | Endpoint exists, updates correctly, validates input |
| FR-02 | Add pagination support to `GET /todos` (page, per_page params) | Easy | Pagination works, returns total count, links |
| FR-03 | Add due_date field to todos with automatic overdue flag | Medium | Field in schema, API accepts, overdue computed |
| FR-04 | Add search/filter by status (`GET /todos?status=completed`) | Easy | Filter works, combined with pagination |
| FR-05 | Add user registration endpoint (`POST /auth/register`) | Medium | Creates user, hashes password, returns token |
| FR-06 | Add refresh token endpoint (`POST /auth/refresh`) | Medium | Rotates tokens, invalidates old ones |
| FR-07 | Add role-based access control (admin, editor, viewer roles) | Hard | Middleware enforces per-endpoint roles |
| FR-08 | Add audit logging (log all state-changing operations) | Medium | Logs user, action, timestamp, diff |
| FR-09 | Add rate limiting per-user (not per-IP) | Medium | Rate limit keyed on user_id, configurable limits |
| FR-10 | Add soft delete for todos (`deleted_at` field) | Medium | Records hidden from GET, admin can view |
| FR-11 | Add CSV export endpoint (`GET /todos/export?format=csv`) | Easy | Returns CSV, headers match fields, proper escaping |
| FR-12 | Add batch create endpoint (`POST /todos/batch`) | Medium | Accepts array, returns created IDs, partial failure handling |
| FR-13 | Add webhook notification on todo completion | Hard | POST to configured URL, retry on failure, idempotency |
| FR-14 | Add tag system (create tags, assign to todos, filter by tag) | Hard | Tags table, many-to-many, CRUD, filter |
| FR-15 | Add sorting by any field (`GET /todos?sort=created_at&order=desc`) | Medium | Whitelist sortable fields, sanitize order |
| FR-16 | Add request ID tracing (X-Request-ID header) | Easy | Middleware generates/injects, logs include it |
| FR-17 | Add WebSocket endpoint for real-time todo updates | Hard | WS auth, event emission on CRUD, reconnection |
| FR-18 | Add "undo delete" endpoint (restore from soft delete) | Medium | Restores soft-deleted record, returns restored data |
| FR-19 | Add API version header validation (Accept-Version) | Easy | Middleware checks, returns 400 on unsupported version |
| FR-20 | Add caching layer for GET endpoints (Redis-like interface) | Hard | Cache-aside pattern, TTL configurable, invalidation on write |

### 3.3 Refactors (20)

All refactors target the same spaghetti codebase (a monolithic 2000-line Flask app with no tests).

| ID | Refactor Description | Risk | Success Criteria |
|----|---------------------|------|-----------------|
| RF-01 | Extract database logic from routes into a service layer | Low | Routes call services, services call DB, tests pass |
| RF-02 | Replace all `print()` statements with proper logging | Low | Logging configured, log levels used, no `print()` remains |
| RF-03 | Add type hints to all function signatures | Low | Every function has types, mypy passes in strict mode |
| RF-04 | Split monolithic `app.py` into separate modules (routes, models, services) | Medium | Imports work, no circular deps, app starts |
| RF-05 | Replace `requests` library with `httpx` (synchronous to async) | Medium | All external calls async, connection pooling, tests pass |
| RF-06 | Add Pydantic models for all request/response validation | Medium | No raw dict access, validation errors return 422 |
| RF-07 | Replace string formatting in SQL with parameterized queries | High | All queries parameterized, no interpolation, tests pass |
| RF-08 | Add proper error handling middleware (remove try/except from routes) | Medium | Global exception handler, structured error responses |
| RF-09 | Extract configuration from hardcoded constants to env variables | Low | No hardcoded config, env file loaded, defaults exist |
| RF-10 | Add database migration system (replace raw SQL with Alembic) | High | Migrations work, up/down reversible, no data loss |
| RF-11 | Replace Flask with FastAPI (full framework migration) | High | Same API surface, async endpoints, auto docs, tests pass |
| RF-12 | Add unit tests for all service layer functions | Medium | 80%+ coverage, tests isolate with mocks |
| RF-13 | Add integration tests for all API endpoints | Medium | Every endpoint tested, test DB isolated, CI runs them |
| RF-14 | Replace custom auth with JWT middleware library | Medium | Auth works, tokens validate, existing users migrate |
| RF-15 | Extract business logic from views into use case classes | Medium | Use cases testable independently, views thin |
| RF-16 | Add health check endpoint that doesn't depend on database | Low | Health check returns OK even when DB is down |
| RF-17 | Add structured logging (JSON format) for log aggregation | Low | Log output is JSON, parsable, includes request_id |
| RF-18 | Replace magic numbers with named constants | Low | No magic numbers, constants file, lint passes |
| RF-19 | Add request timeout middleware for all routes | Medium | Timeout applies, returns 503, configurable per route |
| RF-20 | Add OpenAPI schema documentation decorators to all endpoints | Medium | Every endpoint documented, schema accurate, Swagger works |

---

## 4. Evaluation Criteria

### 4.1 Scoring Rubric

Each criterion is scored 0-100 by an independent judge model (GPT-4o or Claude Sonnet — the one NOT used in generation).

| Criterion | Weight | Scoring Method |
|-----------|--------|---------------|
| **Correctness** | 40% | Judge checks each acceptance criterion: pass (100), partial (50), fail (0). Averaged across all criteria for the task. |
| **Test Pass Rate** | 20% | If tests are generated: pass rate of generated tests. If not: judge assesses test-worthiness of the output. |
| **Security** | 15% | Count of security vulnerabilities found by automated scanning (bandit, semgrep). 100 = 0 vulns. Deduct 10 per low, 20 per medium, 50 per high, 100 per critical. |
| **Maintainability** | 10% | Automated lint score (ruff/pylint): 100 = all checks pass, 0 = no checks pass. |
| **Latency** | 10% | Normalized: fastest condition gets 100. Each condition scored as `(fastest_time / this_time) * 100`. |
| **Cost** | 5% | Normalized: cheapest condition gets 100. Each condition scored as `(cheapest_cost / this_cost) * 100`. |

### 4.2 Judge Model Prompt

```markdown
You are evaluating code quality for a benchmark study. You will receive:
1. A task description
2. The generated code output
3. The acceptance criteria

Your job is to score each acceptance criterion as PASS (100), PARTIAL (50), or FAIL (0).

Rules:
- PASS = the code fully satisfies the criterion
- PARTIAL = the code addresses the criterion but has minor issues
- FAIL = the criterion is not met

You are evaluating FUNCTIONAL CORRECTNESS only, not code style.
Do not penalize for documentation or unused imports unless the criterion requires it.
Be strict. If the code would not work as described, mark it FAIL.
```

### 4.3 Human Calibration

- 20% of all evaluations are spot-checked by a human engineer
- If judge and human disagree on >10% of spot-checks, recalibrate the judge prompt
- Disagreement threshold: Cohen's kappa < 0.8 triggers recalibration

---

## 5. Benchmark Runner Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Benchmark Runner                                │
│                                                                       │
│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────┐   │
│  │  Task Loader  │──▶│  Condition Router │──▶│  Execution Engine   │   │
│  │               │   │                  │   │                     │   │
│  │ Reads from    │   │ A: Single Claude │   │ Python asyncio pool │   │
│  │ benchmark.db  │   │ B: Single Mini   │   │ Configurable        │   │
│  │ 60 tasks      │   │ C: AgentForge    │   │ concurrency (3)     │   │
│  │               │   │ D: Ablation      │   │ Timeout: 10 min     │   │
│  └──────────────┘   └──────────────────┘   └──────────┬──────────┘   │
│                                                        │              │
│  ┌──────────────────┐   ┌──────────────────┐           │              │
│  │  Result Writer   │◀──│  Evaluator       │◀──────────┘              │
│  │                  │   │                  │                           │
│  │ Writes to        │   │ Judge LLM call   │                           │
│  │ benchmark.db     │   │ Human calib      │                           │
│  └──────────────────┘   └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.1 Components

#### Task Loader
```
Input: benchmark.db (tasks table)
Output: Task objects injected into execution context

Task {
    id: str (e.g. "BF-01")
    category: "bug_fix" | "feature" | "refactor"
    codebase_path: str (path to repo snapshot)
    description: str
    acceptance_criteria: list[str]
    severity/cost/risk: str (metadata)
}
```

#### Condition Router
```
For each task, creates 4 execution contexts:

Condition A (Single Claude):
    - Creates a single Claude Sonnet call
    - System prompt: "You are a senior engineer. Write code to satisfy the following requirements."
    - User prompt: task description + codebase context

Condition B (Single Mini):
    - Same structure, uses GPT-4o-mini
    - Controls for: "is the team better, or just using a better model?"

Condition C (AgentForge Team):
    - Runs the full AgentForge LangGraph with 3 agents
    - Team Lead (Gemini Pro) → Builder (Claude Sonnet) → Reviewer (GPT-4o)

Condition D (Ablation — Same Model Team):
    - Same graph, all 3 agents use Claude Sonnet
    - Isolates: "does the multi-agent ARCHITECTURE help, even without model diversity?"
```

#### Execution Engine
```
- Python asyncio with semaphore (max 3 concurrent runs)
- Each run gets:
  - Fresh git checkout of the codebase
  - Environment variables for API keys
  - 10-minute wall-clock timeout
  - Automatic retry on infrastructure failure (not on quality failure)

Output per run:
  - Raw agent output (messages)
  - Generated files
  - Execution metadata (latency, tokens used, cost)
  - Execution log (errors, retries, warnings)
```

#### Evaluator
```
- Calls judge LLM per task per condition (960 judge calls: 240 runs × 4 conditions)
- Judge is the model NOT used in generation (or GPT-4o if Claude was used)
- Judge receives: task description, acceptance criteria, generated code
- Judge returns: scores per criterion, reasoning
- Human spot-check: 20% random sample reviewed by human engineer

Output per evaluation:
  - Per-criterion scores
  - Overall score
  - Security vulnerability count
  - Lint score (ruff run)
  - Judge reasoning
```

### 5.2 Execution Flow

```
1. Pre-flight
   ├── Clone reference codebase (todo-app)
   ├── Install all dependencies
   ├── Run existing tests → confirm baseline
   └── Create 4 task queues (one per condition)

2. Execution
   for each task in queue:
       for each condition (A, B, C, D):
           run = Run(task, condition)
           run.execute()
           run.save_raw_output()
           run.save_metrics()

3. Evaluation
   for each run:
       evaluation = Judge(run.task, run.output)
       evaluation.save()
   
   for 20% random sample:
       human_review(run.task, run.output, blind=True)
       compare human vs judge scores

4. Analysis
   compute_statistics(all_evaluations)
   generate_report()
```

### 5.3 Parallelism & Isolation

- Each run gets a fresh working directory (copy of codebase)
- Concurrent runs use different working directories
- API calls are distributed across API keys to avoid rate limiting
- Maximum 3 concurrent tasks (to avoid overwhelming rate limits)

---

## 6. Result Storage Schema

```sql
-- ============================================================
-- Benchmark Schema — agentforge_benchmarks database
-- Separate from main product database
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Reference tasks
CREATE TABLE benchmark_tasks (
    id                  VARCHAR(20) PRIMARY KEY,  -- "BF-01", "FR-15", etc.
    category            VARCHAR(20) NOT NULL CHECK (category IN ('bug_fix', 'feature', 'refactor')),
    title               VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    codebase_path       VARCHAR(500) NOT NULL,    -- Path to git repo snapshot
    acceptance_criteria JSONB NOT NULL,            -- ["criterion 1", "criterion 2"]
    severity            VARCHAR(20),               -- For bugs: crash, security, logic, data, ux
    complexity          VARCHAR(20),               -- For features: easy, medium, hard
    risk                VARCHAR(20),               -- For refactors: low, medium, high
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Individual benchmark runs
CREATE TABLE benchmark_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             VARCHAR(20) NOT NULL REFERENCES benchmark_tasks(id),
    condition           VARCHAR(10) NOT NULL CHECK (condition IN ('A', 'B', 'C', 'D')),
    model_assignments   JSONB NOT NULL,             -- {"team_lead": "gemini-1.5-pro", ...}
    
    -- Raw output
    raw_output          JSONB,                      -- Full agent output
    generated_files     JSONB,                      -- {"path": "content", ...}
    execution_log       JSONB,                      -- Steps, errors, retries
    
    -- Metrics
    latency_seconds     NUMERIC(10, 2),
    total_tokens_in     INTEGER,
    total_tokens_out    INTEGER,
    total_cost          NUMERIC(12, 6),             -- USD
    
    -- Evaluation results (populated by Evaluator)
    correctness_score   NUMERIC(5, 2),              -- 0-100
    test_pass_rate      NUMERIC(5, 2),              -- 0-100
    security_count      INTEGER,                    -- Total vulns found
    security_score      NUMERIC(5, 2),              -- 0-100 (derived)
    maintainability_score NUMERIC(5, 2),            -- 0-100
    latency_score       NUMERIC(5, 2),              -- 0-100 (normalized)
    cost_score          NUMERIC(5, 2),              -- 0-100 (normalized)
    overall_score       NUMERIC(5, 2),              -- 0-100 (weighted)
    
    -- Judge metadata
    judge_model         VARCHAR(100),                -- Model used to evaluate
    judge_reasoning     TEXT,                        -- Raw judge output
    judge_confidence    NUMERIC(3, 2),              -- Self-reported confidence
    
    -- Human calibration
    human_reviewed      BOOLEAN NOT NULL DEFAULT FALSE,
    human_score         NUMERIC(5, 2),              -- 0-100
    human_notes         TEXT,
    human_vs_judge_diff NUMERIC(5, 2),              -- Absolute difference
    
    -- Run metadata
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

-- Criteria-level scores (for granular analysis)
CREATE TABLE benchmark_criteria_scores (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    criterion_index     INTEGER NOT NULL,           -- Index into acceptance_criteria array
    criterion_text      TEXT NOT NULL,
    score               NUMERIC(5, 2) NOT NULL,     -- 0, 50, or 100
    judge_reasoning     TEXT
);

-- Run security findings
CREATE TABLE benchmark_security_findings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    severity            VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    title               VARCHAR(500) NOT NULL,
    file_path           VARCHAR(500),
    description         TEXT
);

-- Indexes for analysis queries
CREATE INDEX idx_runs_task ON benchmark_runs(task_id);
CREATE INDEX idx_runs_condition ON benchmark_runs(condition);
CREATE INDEX idx_runs_status ON benchmark_runs(status);
CREATE INDEX idx_runs_overall ON benchmark_runs(overall_score);
CREATE INDEX idx_criteria_run ON benchmark_criteria_scores(run_id);
```

### Query Examples

```sql
-- Average correctness by condition
SELECT condition, AVG(correctness_score) AS mean, STDDEV(correctness_score) AS std
FROM benchmark_runs
WHERE status = 'completed'
GROUP BY condition
ORDER BY condition;

-- Which tasks does the team win on most?
SELECT task_id,
       AVG(CASE WHEN condition = 'C' THEN overall_score END) AS team_score,
       AVG(CASE WHEN condition = 'A' THEN overall_score END) AS single_score,
       AVG(CASE WHEN condition = 'C' THEN overall_score END)
       - AVG(CASE WHEN condition = 'A' THEN overall_score END) AS delta
FROM benchmark_runs
WHERE status = 'completed'
GROUP BY task_id
ORDER BY delta DESC;

-- Security findings by condition
SELECT condition, severity, COUNT(*) AS count
FROM benchmark_runs r
JOIN benchmark_security_findings f ON f.run_id = r.id
GROUP BY condition, severity
ORDER BY condition, severity;
```

---

## 7. Reporting Dashboard

### 7.1 Executive Summary Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  BENCHMARK DASHBOARD                  Status: 240/240 Runs Complete │
│  Last updated: 2026-07-01 14:30 UTC                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │ Overall Winner       │  │ Best Condition       │                   │
│  │ Condition C          │  │ Team Win Rate: 65%   │                   │
│  │ (AgentForge Team)    │  │ vs Single: 35%       │                   │
│  │ Score: 82.4/100      │  │ Ties: 0%             │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Score by Condition                                            │   │
│  │                                                               │   │
│  │  100 ┤                                                     █  │   │
│  │      │                                           ██████ █  █  │   │
│  │   80 ┤                                █████████ ██████ ██ █  │   │
│  │      │                 █████████████ ██████████ █████████ ██  │   │
│  │   60 ┤   ███████████ ██████████████ ███████████ ███████████  │   │
│  │      │   ██████████████████████████████████████████████████  │   │
│  │   40 ┤   ██████████████████████████████████████████████████  │   │
│  │      │                                                       │   │
│  │       ─────────────────────────────────────────────────────  │   │
│  │          A            B            C            D             │   │
│  │        Single       Single      AgentForge   Ablation        │   │
│  │        Claude        Mini         Team       (All Claude)    │   │
│  │       68.2          41.5         82.4         74.1            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Detailed Analysis Pages

#### 7.2.1 By Category

```
┌─────────────────────────────────────────────────────────────────────┐
│  SCORE BY CATEGORY                                                   │
│                                                                      │
│  ┌──────────────┬──────────┬──────────┬──────────┬──────────┐       │
│  │ Category     │ A (Claude)│ B (Mini) │ C (Team) │ D (Abl.) │       │
│  ├──────────────┼──────────┼──────────┼──────────┼──────────┤       │
│  │ Bug Fixes    │   72.1   │   38.4   │   85.3   │   76.2   │       │
│  │ Features     │   65.8   │   42.1   │   80.7   │   72.9   │       │
│  │ Refactors    │   66.7   │   44.0   │   81.2   │   73.2   │       │
│  └──────────────┴──────────┴──────────┴──────────┴──────────┘       │
│                                                                      │
│  Insight: Team advantage is consistent across all categories.       │
│  Largest gap: Bug Fixes (+13.2 pts vs Single Claude).                │
└─────────────────────────────────────────────────────────────────────┘
```

#### 7.2.2 By Evaluation Criterion

```
┌─────────────────────────────────────────────────────────────────────┐
│  SCORE BY CRITERION                                                  │
│                                                                      │
│  Criterion        A (Claude)  B (Mini)  C (Team)  D (Abl.)  Weight  │
│  ─────────────────────────────────────────────────────────────       │
│  Correctness      72.4        44.1       85.6       76.8      40%    │
│  Test Pass Rate   60.2        31.8       78.3       70.1      20%    │
│  Security         65.0        38.0       82.0       72.0      15%    │
│  Maintainability  71.5        50.2       76.4       74.8      10%    │
│  Latency          95.0        98.0       65.0       68.0      10%    │
│  Cost             75.0        98.0       82.0       80.0       5%    │
└─────────────────────────────────────────────────────────────────────┘
```

#### 7.2.3 Security Deep Dive

```
┌─────────────────────────────────────────────────────────────────────┐
│  SECURITY FINDINGS BY CONDITION                                      │
│                                                                      │
│  Severity     A (Claude)  B (Mini)  C (Team)  D (Ablation)          │
│  ─────────────────────────────────────────────────────────           │
│  Critical          3          12         0           2               │
│  High             12          28         3          10               │
│  Medium           18          35         8          15               │
│  Low              25          42        15          22               │
│  ─────────────────────────────────────────────────────────           │
│  Total            58         117        26          49               │
│                                                                      │
│  Insight: Team catches 55% more vulnerabilities than single Claude. │
│  Critical vulnerabilities eliminated entirely by team.               │
└─────────────────────────────────────────────────────────────────────┘
```

#### 7.2.4 Cost vs Quality Tradeoff

```
┌─────────────────────────────────────────────────────────────────────┐
│  COST vs QUALITY SCATTER                                            │
│                                                                      │
│  Quality │  ┌───┐                                                    │
│    90    │  │ C │                                   Best quality     │
│          │  └───┘                                   per dollar?      │
│    80    │      ┌───┐                                                │
│          │      │ D │                                                │
│    70    │          ┌───┐                                            │
│          │          │ A │                                            │
│    60    │          └───┘                                            │
│          │                                                           │
│    50    │              ┌───┐                                        │
│          │              │ B │                                        │
│    40    │              └───┘                                        │
│          └──────────────────────────────────────                     │
│            0.01    0.05    0.10    0.15    0.20                      │
│                              Cost ($)                                │
│                                                                      │
│  C: $0.091/task  →  82.4 quality  →  905 quality-per-dollar         │
│  A: $0.035/task  →  68.2 quality  →  1949 quality-per-dollar        │
│                                                                      │
│  Insight: Team costs 2.6x more but delivers 1.2x quality.           │
│  Quality-per-dollar is lower for the team.                           │
│  BUT: team catches 3x more critical security issues.                 │
└─────────────────────────────────────────────────────────────────────┘
```

#### 7.2.5 Ablation Analysis

```
┌─────────────────────────────────────────────────────────────────────┐
│  ABLATION ANALYSIS: Does multi-agent architecture help?              │
│                                                                      │
│  Condition D (all Claude) vs Condition A (single Claude)             │
│                                                                      │
│  Same model. Different architecture.                                 │
│                                                                      │
│  Metric              Single    Team (same model)  Delta   p-value    │
│  ─────────────────────────────────────────────────────────           │
│  Correctness         72.4      76.8               +4.4   0.031*      │
│  Test Pass Rate      60.2      70.1               +9.9   0.008**     │
│  Security            65.0      72.0               +7.0   0.042*      │
│                                                                      │
│  * p < 0.05  ** p < 0.01                                             │
│                                                                      │
│  Verdict: Multi-agent architecture ALONE provides significant       │
│  improvement even when all agents use the same model.               │
│  Adding model diversity (C) amplifies the effect further.           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Statistical Analysis Method

### 8.1 Primary Analysis

**Test:** Paired one-tailed t-test (or Wilcoxon signed-rank if normality fails)

**Comparison:** Condition C vs Condition A

**Per-task pairing:** Each task is evaluated under both conditions. The paired design controls for task difficulty variance.

**Formula:**
```
t = (mean_diff) / (std_diff / sqrt(n))
where:
  mean_diff = mean(C_score - A_score) across all 60 tasks
  std_diff = standard deviation of the differences
  n = 60 (number of paired observations)
```

**Normality check:** Shapiro-Wilk test on the differences. If p < 0.05, use Wilcoxon signed-rank instead.

**Effect size (Cohen's d):**
```
d = mean_diff / std_diff
d = 0.2 (small), 0.5 (medium), 0.8 (large)
```

### 8.2 Secondary Analysis

| Test | Purpose |
|------|---------|
| McNemar's test | Compare binary pass/fail rates between conditions |
| Chi-square | Compare security finding distributions |
| ANOVA (repeated measures) | Compare all 4 conditions simultaneously |
| Post-hoc Tukey HSD | Which specific condition pairs are significantly different? |

### 8.3 Multiple Comparison Correction

- 4 conditions → 6 pairwise comparisons
- Apply **Bonferroni correction**: α = 0.05 / 6 = 0.0083
- Report raw p-values AND adjusted significance

### 8.4 Required Sample Size

**Power analysis (pre-hoc):**
- Desired power: 0.80
- Significance level: 0.05 (Bonferroni-corrected: 0.0083)
- Expected effect size: d = 0.5 (medium, from pilot data)
- Required n per condition: **n = 27** (for 80% power detecting d=0.5)

With n = 60 per condition, we have **>95% power** to detect d = 0.5.

### 8.5 Reporting Template

```
=== BENCHMARK RESULTS: Condition C (Team) vs Condition A (Single Claude) ===

PRIMARY METRIC: Correctness
  Mean (Team):     85.6 (SD: 12.3)
  Mean (Single):   72.4 (SD: 15.1)
  Mean Diff:      +13.2 (95% CI: [9.8, 16.6])
  t-statistic:     7.84
  p-value:         0.0000012
  Cohen's d:       0.98 (large effect)
  Significance:    ✅ p < 0.0083 (Bonferroni corrected)

SECONDARY METRICS:
  Test Pass Rate:  +18.1 (p = 0.0008) ✅
  Security:        -32 findings (p = 0.0021) ✅
  Maintainability: +4.9 (p = 0.062) ❌ (not significant)

VERDICT: H0 REJECTED.
  AgentForge teams significantly outperform single Claude Sonnet
  on correctness, test quality, and security.
  Maintainability difference not statistically significant.
```

---

## 9. Success Thresholds

### 9.1 Go / No-Go Criteria

| Threshold | Metric | Target | Result |
|-----------|--------|--------|--------|
| **P0 — Must pass** | Correctness (C vs A) | Team > Single by ≥10 points | TBD |
| **P0 — Must pass** | Statistical significance | p < 0.05 after correction | TBD |
| **P0 — Must pass** | Security (C vs A) | Team catches ≥2x vulns | TBD |
| **P1 — Should pass** | Ablation (D vs A) | Multi-agent > Single by ≥5 pts | TBD |
| **P1 — Should pass** | Human calibration | Cohen's kappa > 0.8 | TBD |
| **P2 — Nice to have** | Cost efficiency | Team quality-per-dollar > 80% of single | TBD |

### 9.2 Decision Matrix

| Correctness | Security | Ablation | Verdict |
|-------------|----------|----------|---------|
| ✅ Pass | ✅ Pass | ✅ Pass | **GO** — Multi-model hypothesis strongly proven |
| ✅ Pass | ✅ Pass | ❌ Fail | **GO** — Model diversity matters more than architecture |
| ✅ Pass | ❌ Fail | ✅ Pass | **CAUTION** — Team produces better code but not more secure |
| ❌ Fail | ✅ Pass | ✅ Pass | **CAUTION** — Team is more secure but not more correct |
| ❌ Fail | ❌ Fail | ✅ Pass | **HOLD** — Architecture helps but not enough to justify cost |
| ❌ Fail | ❌ Fail | ❌ Fail | **NO GO** — Hypothesis falsified. Pivot or kill. |

### 9.3 Expected Outcomes by Scenario

| Scenario | Correctness (C vs A) | Security | Cost Multiple | Recommendation |
|----------|---------------------|----------|---------------|---------------|
| Strong win | +15-20 pts | 3x fewer vulns | 2.5-3x | Build product. Raise money. |
| Moderate win | +8-14 pts | 2x fewer vulns | 2.5-3x | Ship but optimize cost |
| Weak win | +3-7 pts | 1.5x fewer vulns | 2.5-3x | Pivot to enterprise (compliance) |
| No diff | 0 ± 3 pts | Same | 2.5-3x | Kill product or pivot entirely |
| Single wins | Single is better | Single is better | 2.5-3x | Kill product immediately |

### 9.4 What We Learn From Each Outcome

| Outcome | What it means for the business |
|---------|-------------------------------|
| ❌ Hypothesis falsified | AgentForge (as AI team platform) has no product-market fit. Pivot to: AI governance, compliance monitoring, or enterprise model routing. The "teams" feature is a differentiator, not the core. |
| ⚠️ Weak win (quality) | The team produces marginally better code but at 2.5-3x cost. This doesn't work for consumers/startups. Pivot to enterprise where security/compliance justifies the cost overhead. |
| ✅ Moderate win | The team is meaningfully better. Position as: "Better quality, built-in review, security audit." Target devs who value quality over speed. |
| 🏆 Strong win | The team is dramatically better. Position as: "AI teams produce better code than any single AI." This is the category-defining result. Raise money, hire fast, build the category. |

---

## 10. Implementation Plan

### Build Effort: 5-7 days

| Day | Task |
|-----|------|
| 1 | Create benchmark database schema + seed 60 tasks |
| 2 | Build benchmark runner (task loader, condition router, execution engine) |
| 3 | Build evaluator (judge LLM integration, scoring logic) |
| 4 | Set up codebase snapshots (todo-app repo with all bug versions) |
| 5 | Dry-run benchmark on 10 tasks to validate pipeline |
| 6 | Run full benchmark (240 runs, ~12 hours) |
| 7 | Analyze results, generate report, build dashboard |

### Integration Points

- Benchmark runner lives at `apps/benchmark/` (separate from main app)
- Shares `core/providers.py` for AI model calls
- Uses its own database (`agentforge_benchmarks`)
- No dependency on main product API (isolated, can run independently)
- Results feed into `docs/BENCHMARK_RESULTS.md` for investor/team communication

---

## 11. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI provider API changes mid-benchmark | Invalidates comparison | Pin model versions; run all conditions interleaved (not sequentially) |
| Judge model bias (prefers certain model outputs) | Skews scores | Use different judge than generators; shuffle outputs; human calibration |
| Codebase snapshot diverges from task description | Invalid task | Automated validation: each task has a test that confirms the bug/feature gap |
| Rate limiting delays execution | Time cost | Distribute across API keys; max 3 concurrent; budget 24h for full run |
| Statistical significance not reached | Inconclusive | 60 tasks provides >95% power for medium effect sizes. If inconclusive, run more tasks. |
| Human calibration fails (judge disagrees with human) | Untrustworthy scores | Re-prompt judge with calibration examples. If still fails, use human-only evaluation for the 20% sample and extrapolate. |
