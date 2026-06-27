# AgentForge — Execution Roadmap (2026-06-26)

Prioritization order: **(1) trustworthiness/correctness → (2) one real wedge → (3) proof of value →
(4) retention/data flywheel → (5) scale**. Do not build new surface area until P0/P1 correctness is fixed.

## 30 days — "Stop the bleeding, ship the wedge"
**Goal:** safe to run multi-tenant; Quick Review is the product.
- Fix file-download & task-creation IDOR; audit every `project_files`/`tasks` query for ownership (P0/P1).
- Add Redis to docker-compose; assert it on boot.
- Refresh-token revocation + `/logout`; move auth to HttpOnly cookies; add client route guards.
- Add `tasks/executions(created_by)` indexes; advisory lock around boot migrations.
- Prompt-injection mitigation: delimit user/file content, cap `repository_context` length.
- Make CI lint/security gates blocking; pin `cryptography/bcrypt/PyJWT`.
- Persist Quick-Review history server-side (first retention hook).
- **Exit criteria:** an external user can `docker compose up`, sign up, run Quick Review, and no
  authenticated user can read another tenant's data.

## 90 days — "Be where developers work + prove value"
**Goal:** distribution + the first honest quality number.
- **GitHub App / PR review bot** powered by Quick Review (comment findings inline on PRs).
- **CLI** (`agentforge review <files>`); optional IDE wrapper.
- Collapse the 4-reviewer fan-out to a **1–2 critic + repair loop**; wire retrieved memory into
  builder + critic; cut token cost.
- **Honest benchmark:** curate a labeled bug dataset (or SWE-bench-lite subset), run single-model vs
  pipeline, publish real precision/recall. Retire the hardcoded "40%".
- Externalize rate-limit/metrics to Redis; offload blocking file I/O.
- Route-level + failure-path tests for `/projects`,`/context`; enforce a coverage floor.
- **Exit criteria:** a real number you'd show an investor without flinching, and a PR bot that a
  team uses daily.

## 6 months — "Differentiate via the data flywheel"
**Goal:** something incumbents don't have for your users.
- Capture accept/reject signal on every finding → train/condition the critic on it (the moat).
- pgvector-backed semantic memory that measurably improves repeat-repo runs.
- Sandboxed test execution (make `tester` real and trustworthy).
- Team/org workspaces with **real RBAC** (currently absent) + shared memory.
- Repo-aware multi-file edits (clone → plan → patch → PR) as a beta.
- Observability: OpenTelemetry tracing; metrics to a real TSDB.

## 12-month vision
A **trustworthy, in-workflow code-quality layer** for teams: every PR gets a multi-lens review that
**gets smarter from your team's own accept/reject history**, with optional agentic fixes. The bet is
not "more agents" — it's a **proprietary quality flywheel** + frictionless distribution
(GitHub/CLI/IDE). Monetization: per-seat team tier (shared memory, RBAC, PR bot, analytics);
self-host for enterprise. Win condition: a team's reviews are demonstrably better *because* they use
AgentForge, in a way a generic Claude/GPT call can't replicate without their data.

## What to explicitly NOT do
- Don't add more agents to the pipeline.
- Don't ship the `/demo` simulation as if it's the product.
- Don't publish any quality number you didn't measure.
- Don't build org/RBAC features before authorization correctness is fixed.
