# Developer Experience Gap Report

**Scope:** What does it feel like to use AgentForge as a working developer
every day? Three surfaces: the **web app**, the **CLI**, and the **REST
API**. Plus the onboarding ramp, the templates flow, and the feedback
loop. The question is not "does the feature exist" — it usually does — but
"is it pleasant enough that I reach for AgentForge before reaching for
Cursor?"

**Verdict:** AgentForge is technically usable but **adoption-fragile**. The
landing page is polished; the dashboard works; the CLI handles `review`
cleanly. But the path from "I have a feature to build" to "the agents are
working on it" is six forms and a polling page. There is no
"agentforge-on-the-keyboard" ergonomic surface, no real-time streaming,
no in-PR comments, and no way to *trust* that an agent run actually
changed the right files.

---

## 1. The Three Surfaces, Honestly Assessed

### Web App

**Strengths:**

- Polished landing page (`apps/web/app/page.tsx`, 413 lines) with a
  frictionless "paste code, get a review" path that requires no account.
- Decent typography and motion. Framer Motion is used sparingly.
- Command palette (`components/command-palette.tsx`) for keyboard nav.
- Sidebar + topbar layout is consistent.
- The dashboard, tasks list, analytics, and teams pages render.
- Good use of `cn()` helper, `MetricCard`, `Badge` primitives.

**Weaknesses:**

1. **Polling, not streaming.** The task detail page polls `getTask` /
   `getTaskMessages` / `getExecution` every 600 ms (`page.tsx:194`). On
   any moderately long run this is hundreds of requests per task. The
   websocket handler exists in `apps/api/app/ws/` but the frontend never
   subscribes — there's no `lib/ws-client.ts` wire-up in `app/`.
2. **Six forms before action.** "I want to build a feature" →
   `/dashboard` → `/teams/[id]` → "create task" → title → description →
   confirm. There's no "⌘K → build X" shortcut that goes straight to a
   running task.
3. **No diff view.** The task detail page shows `delivery.content` as
   pretty-printed JSON. It does not show a real `diff` of the changed
   files. The user has to mentally reconstruct the change.
4. **No file tree navigation.** Even though `repository_contexts` and
   `code_chunks` exist, the UI doesn't render a file browser. There's a
   `ContextViewer` component but it's unused in the main flows.
5. **Empty states are weak.** Several pages show "No X yet" without a
   call to action. `register/page.tsx`, `login/page.tsx` show form
   fields; if the user is already authenticated, they should be redirected.
6. **Settings is two pages.** `/settings` and `/settings/providers`. The
   split is arbitrary — there's no "API keys" tab on settings; it's a
   sibling route. No `/settings/members`, no `/settings/billing` (which
   is fine for OSS, but the placeholder route doesn't say so).
7. **Memory viewer is not semantic search.** `components/memory-viewer.tsx`
   lists memories; you can't ask "what did we learn about authentication?"
   and get back a relevance-ordered set.
8. **No real-time presence.** Two users on the same project? No indicator.
   No "Alice is editing this task right now". This matters for team
   adoption.
9. **Onboarding doesn't exist in-app.** The `docs/development/ONBOARDING.md`
   is great, but there's no "Welcome, here's your first task" panel inside
   the app itself.

### CLI

**Strengths:**

- Clean argparse, single binary, installable via pip (`pip install -e
  apps/cli`).
- `agentforge review file.py` returns a non-zero exit code when there are
  blocking findings (`__main__.py:_print_issues`). This is **excellent**
  for shell scripting — it can be wired into pre-commit.
- Tokens stored on disk (refresh + access split).
- Severity sorting in `_print_issues` is sane.

**Weaknesses:**

1. **No streaming output.** `client.review_and_wait` blocks until done.
   For long tasks there is no progress indicator. The CLI feels frozen.
2. **No `init` or `setup` command.** First-time setup is "edit your env,
   login, pray". A real CLI does `agentforge init`, asks for the API URL,
   logs you in, validates the connection, and writes the config.
3. **No `--format json` or `--format sarif`.** Reviews only print to
   stdout in a human layout. SARIF would let the CLI plug into GitHub
   code scanning for free.
4. **No `apply` subcommand.** A finding has a `suggestion`. There's no
   `agentforge review --apply-suggestions file.py` that writes the patch
   in place. The reviewer tells you what to fix but doesn't help you
   apply it.
5. **`task` subcommand has no `--wait` or `--follow`.** You create a task
   and have to re-run `agentforge status <id>` in another shell. There
   is no `agentforge task --watch`.
6. **No `agentforge diff <task-id>`.** Once a task completes, the CLI
   cannot show you what files the agents edited.
7. **No project context.** The CLI doesn't know about your project, your
   team, your templates. It only knows about a file you hand it.
8. **Tests cover the trivial path.** `test_cli.py` exists but only
   exercises `cmd_review`. Login / logout / task / status paths are
   undertested.

### REST API

**Strengths:**

- OpenAPI/Swagger UI at `/docs`.
- Pydantic v2 schemas everywhere.
- Sensible versioning (`/api/v1`).
- Refresh-token rotation implemented.
- Async throughout (FastAPI + asyncpg).
- Tenant isolation enforced on every route.

**Weaknesses:**

1. **No SDK generated.** The web app hand-rolls 533 lines of `api.ts`.
   There's no `agentforge-sdk` (TS or Python). Every consumer reinvents
   auth, retries, pagination.
2. **No pagination on `list_tasks`.** Looking at the routes, several list
   endpoints return all rows in one shot. This breaks the moment a team
   has 100 tasks.
3. **No filtering DSL.** `GET /tasks?status=running&team_id=X` is fine,
   but `GET /tasks?since=2026-06-01&fingerprint=…` would be better.
4. **No rate-limit headers.** A client cannot tell when it should back
   off. There's probably a global limit somewhere but it's invisible.
5. **Idempotency keys missing.** `POST /review` is non-idempotent.
   Double-submit creates two reviews.
6. **Webhooks are not first-class.** GitHub has webhooks; the API does
   not expose outbound webhooks for "task completed", "review found
   critical", etc. Power users want to chain AgentForge into their CI.

---

## 2. Onboarding Ramp

**Today:** A new user must:

1. Clone the repo, copy `.env.example`, fill in 6 keys (DB, Redis,
   OpenAI/Anthropic, GitHub, JWT secrets).
2. `docker compose up -d` for Postgres+Redis.
3. `pnpm install` in three workspaces.
4. `pnpm db:migrate` (separate package).
5. `pnpm dev:api` and `pnpm dev:web` in two terminals.
6. Open `http://localhost:3000`, register an account, create a team,
   upload files (optional), and finally create a task.

This is **9 steps** for the first useful output. The `ONBOARDING.md`
doc helps, but the underlying ergonomics are still 9 steps. Real CLIs
deliver a first successful command in **3 steps** (`pip install`, `init`,
`run`).

**Target:** 3 steps.

1. `pip install agentforge` (CLI only) or open the web app.
2. `agentforge init` (CLI) or "Sign in with GitHub" (web).
3. Run a real command on real code.

---

## 3. Templates Flow

`apps/web/app/templates/page.tsx` and `lib/templates.ts` exist. The flow
is: pick a template → fill fields → create a task. This is the right
*shape*. The problem is the templates themselves — they're either too
generic ("build a feature") or too specific ("refactor this auth module")
with no middle ground. There is no community gallery, no versioning, no
forking. Compare to Linear templates, GitHub Actions marketplace, or
Continue.dev slash commands.

---

## 4. Quick Review UX

The `QuickReviewTextarea` / `QuickReviewProgress` / `QuickReviewResults`
components are well-factored. They work in both the landing page and the
dashboard.

But:

- The polling interval is 2s (`dashboard/page.tsx:61`), which is fine for
  the homepage but slow for a developer waiting to paste, review, fix,
  paste again.
- The textarea has no file-drop, no diff paste, no "review the last N
  commits" affordance.
- The result panel shows issues but does not let you click "apply this
  fix" — the developer has to copy-paste by hand.

---

## 5. Cross-Cutting DX Issues

### DX-1 — No keyboard-first path

⌘K opens the command palette. Good. But every important action lives
behind mouse clicks: "create task", "upload file", "review", "configure
team". A power user wants `⌘K → build → enter → type → enter` and a
running task.

### DX-2 — No "what just happened" digest

After a long task, the user lands on `tasks/[id]`. They see messages.
They see a JSON blob. There is no "you changed 3 files in 2 modules;
here is a diff" summary.

### DX-3 — No dark/light theme toggle

Looking at the components, the styling assumes dark. There is no theme
switcher. Many devs prefer light.

### DX-4 — Mobile is barely supported

Layouts are desktop-first. The task detail page has `max-w-4xl mx-auto`
and a grid that collapses on mobile, but the execution graph and message
stream are unusable on a phone.

### DX-5 — No offline / queue mode

If the API is down, the web app throws errors. No "your task is queued
locally and will sync when the API comes back".

### DX-6 — The CLI is a citizen, not a first-class peer

It's nice that the CLI exists. But the CLI doesn't ship with a man page,
shell completion, or `--help` examples. It feels like an afterthought.

---

## 6. Specific Improvements Ranked by Impact

### DX-7 — WebSocket streaming on task detail (P0)

Replace the 600ms `setInterval` poll with a real WS subscription. Add
`apps/web/lib/ws-client.ts` and wire it into the tasks page. Latency
drops from 600ms to <100ms. UX is materially better.

**Effort:** 1 week.

### DX-8 — Generate an SDK (P0)

Use `openapi-typescript-codegen` or `openapi-python-client` to generate
both a TS SDK (for the web app) and a Python SDK (for `apps/cli`). Delete
the hand-rolled `apps/web/lib/api.ts` and the `client.py` and replace
with generated code.

**Effort:** 2 weeks. Pays for itself in maintenance forever.

### DX-9 — Diff view on task delivery (P0)

The Builder already returns `files[]` with `path`, `content`,
`language`. Render a real diff: original (from `repository_contexts`)
vs new (from `BuilderOutput`). Highlight added/removed lines. This is
the single highest-leverage UX change because today users cannot tell
*what* changed.

**Effort:** 2 weeks.

### DX-10 — `agentforge init` + `agentforge task --watch` (P1)

Make the CLI self-bootstrapping. Add `--watch` to `task` so the user
sees live progress and can re-run `review` on the output.

**Effort:** 1 week.

### DX-11 — SARIF output from CLI (P1)

Add `--format sarif`. This unlocks free integration with GitHub Code
Scanning. Every team using GitHub Advanced Security will then have a
free installation path.

**Effort:** 1 week.

### DX-12 — In-app onboarding (P1)

First-run wizard that takes the user through: connect a repo (or skip),
create a team (or use default), pick a template, run the first task.
Track completion in `users.onboarding_completed_at`.

**Effort:** 2 weeks.

### DX-13 — Apply-suggestions in CLI + Web (P1)

For any finding with a `suggestion` and a `file`, allow one-click (web)
or `--apply` (CLI) write-back. This is the difference between "advisory
tool" and "tool that gets used".

**Effort:** 1 week.

### DX-14 — Pagination + filtering on list endpoints (P1)

Cursor-based pagination everywhere. `?since=`, `?fingerprint=`, `?team=`
filters on `/tasks`. Standard `Link: rel="next"` headers.

**Effort:** 1 week.

### DX-15 — Webhooks outbound (P2)

`POST /webhooks` to register a URL for `task.completed`,
`review.critical_found`, etc. Power users integrate AgentForge into CI.

**Effort:** 2 weeks.

---

## 7. What is Already Good

- The Quick Review path is frictionless.
- The CLI exits non-zero on blocking findings — a hugely underrated win.
- The frontend design system is coherent (`ui/*` primitives + `cn()`
  helper).
- Pydantic v2 + FastAPI gives the API excellent types.
- The error boundary (`error-boundary.tsx`) is present.
- Tenant isolation is enforced.

---

## 8. Honest Assessment

AgentForge looks like a polished product. It is not. It is a polished
**demo**. The polish is in the landing page and the dashboard hero
section. The depth is missing everywhere the user spends the other 95%
of their time: inside a long task, inside a multi-file diff, inside the
moment they want to re-run something.

The single most painful DX moment today is **opening a completed task
and not knowing what changed**. That is fixable in two weeks and would
transform how the product feels.

The second most painful is **polling instead of streaming**. That is
fixable in one week and would remove the most common complaint ("why
does it feel so slow?").

Everything else is iteration. These two are existential.