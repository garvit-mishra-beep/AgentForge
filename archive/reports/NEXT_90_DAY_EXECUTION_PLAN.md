# Next 90-Day Execution Plan

**Scope:** The first 90 days of executing the V1 Remaining Roadmap. Week-
by-week deliverables, success metrics, risks, and validation strategy.
Designed for **2 engineers + 1 part-time designer/PM**.

**Verdict:** 90 days is enough to ship a credible V0.5 (the *minimum
useful AgentForge*) and set up V1 beta. The plan is realistic on
engineering effort but tight on dependency management — R-1 (symbol
graph) must land in the first 4 weeks or everything downstream slips.

---

## Team & Cadence

- **2 backend/full-stack engineers** (1 senior, 1 mid). Senior owns
  R-1, A-7, A-8, M-1. Mid owns DX-7, DX-8, G-2, G-3.
- **1 part-time designer/PM** (~50%). Owns UX flows, onboarding, V-1
  benchmark curation.
- **Weekly Monday planning**, **Wednesday demo**, **Friday retro**.
- **Bi-weekly external demo** to a design partner (1 friendly team
  using AgentForge on a real repo).

---

## Week 1–2 — Foundations

### Goals

Stand up the engineering surface for everything that follows. No
visible user value yet; everything is below water.

### Deliverables

- [ ] **R-1 prep**: Migration `018_code_edges.sql` — add
  `code_edges(source_symbol_id, target_symbol_id, kind, confidence)` +
  GIN index on `(source_symbol_id)`. Land migration in CI.
- [ ] **A-7**: Wire `state.review_aggregator_output` →
  `Builder.review_feedback`. Single-edge change. Land with tests.
- [ ] **A-10 prep**: Wrap every node call in
  `parse_structured(schema, retry=True)`. Land util; convert Aggregator
  first.
- [ ] **DX-8 prep**: Stand up `apps/sdk/` workspace; generate TS SDK
  from OpenAPI; replace `apps/web/lib/api.ts` with the generated client
  in *one* route (auth) as proof.
- [ ] **Eval framework stub**: `apps/api/evals/` directory with
  `runner.py`, 5 hand-written PRs as seed fixtures.

### Success Metrics

- Migration 018 applied to staging without error.
- A-7: at least one Builder→Reviewer→Builder regression test exists.
- Generated TS SDK used in `auth` route; `git diff apps/web/app/login`
  shows the import switch.
- 5 eval fixtures passing against `main`.

### Risks

- **R-1 may require parser changes** — if `code_symbols` doesn't have
  the columns we need, the migration slips. *Mitigation:* dry-run
  migration on a snapshot first.

### Validation

- Run `pytest apps/api/tests/test_repository_graph.py` (new).
- Smoke-test A-7 against a known bad-builder scenario.

---

## Week 3–4 — Repository Graph v1

### Goals

The first version of the graph engine is up. Architects and Builders
can answer "what calls this?" queries.

### Deliverables

- [ ] **R-1**: `repo_graph` service with `get_callers(symbol_id)` and
  `get_callees(symbol_id)` using recursive CTEs. Land as
  `apps/api/app/repo_graph.py`.
- [ ] **R-1 wire**: Reviewer prompt receives the list of callers for
  each function it comments on (truncated, fenced via `wrap_context`).
- [ ] **R-2**: `POST /repo/explain` route — runs the Architect node
  over a synthesized view of the parsed repo (top-level modules,
  dependency clusters, language breakdown).
- [ ] **A-10 full**: All seven nodes validate via `parse_structured`
  with retry-on-fail.

### Success Metrics

- `get_callers` returns <50ms p95 over a 10k-symbol fixture.
- Reviewer output on a fixture with cross-file coupling improves
  precision (vs eval set baseline).
- `POST /repo/explain` returns a 5-paragraph layered summary for a
  1k-file Node project.

### Risks

- **Recursive CTE perf** — at >50k symbols, naive recursion is slow.
  *Mitigation:* cap recursion depth, materialize sub-graphs lazily.
- **Architect hallucinates layers** — natural for an LLM. *Mitigation:*
  cross-check claimed layers against top-level directory tree; warn on
  mismatch.

### Validation

- Hand-validate `get_callers` on a known repo (e.g. FastAPI itself).
- Run eval set; verify precision ≥ baseline.

---

## Week 5–6 — Embeddings & Memory v1

### Goals

Replace ILIKE keyword retrieval with cosine similarity. Decision
tracking becomes first-class.

### Deliverables

- [ ] **M-1**: Migration `019_memories_embeddings.sql` — add
  `embedding vector(1536)`, HNSW index. Backfill script for existing
  memories via `text-embedding-3-small`.
- [ ] **M-1 wire**: Replace `get_relevant_memories` keyword branch with
  `<=>` cosine; retain keyword fallback if embedding is null.
- [ ] **M-2**: Migration `020_decisions.sql` + `apps/api/app/decision_service.py` +
  routes `POST /decisions`, `GET /decisions`, `GET /decisions/:id`.
- [ ] **M-2 capture**: When a task's `delivery.verdict == pass` and
  ≥3 files changed, prompt the Team Lead to write an ADR; persist to
  `decisions`.

### Success Metrics

- Embedding backfill runs < 30 min on 10k memories.
- `get_relevant_memories` returns semantically relevant results for 5
  hand-crafted queries (precision@5 ≥ 0.8).
- A passing task produces ≥1 decision record.

### Risks

- **OpenAI embedding cost** for backfill. *Mitigation:* batch with
  `embeddings.create` of 256 at a time; cache by hash.
- **Decision prompt noise** — Team Lead may decline. *Mitigation:*
  `decisions` is opt-in per task (`team_config.auto_adrs`).

### Validation

- Run 10 hand-crafted retrieval queries; manual judgement.
- Trigger 5 passing tasks; verify ≥3 produce decisions.

---

## Week 7–8 — DX Foundations

### Goals

The product stops feeling like a polling demo.

### Deliverables

- [ ] **DX-7**: WebSocket client in `apps/web/lib/ws-client.ts`.
  Replace `setInterval(load, 600)` in `tasks/[id]/page.tsx` with WS
  subscription. Server already has the WS handler.
- [ ] **DX-8 cont**: Generated SDK covers all `/api/v1/*` routes.
  Replace `apps/web/lib/api.ts` with the SDK. Delete the hand-rolled
  file.
- [ ] **DX-9 stub**: Backend exposes `GET /tasks/:id/diff` returning
  per-file diffs (old vs new). Frontend renders a side-by-side diff
  in the task detail page.

### Success Metrics

- WS latency on task detail ≤ 200ms (vs 600ms polling).
- All frontend API calls go through the SDK.
- Diff view renders for 100% of completed tasks that have a Builder
  output.

### Risks

- **WS scaling** — FastAPI WS handlers can be sticky; ensure reverse
  proxy supports it. *Mitigation:* docs note.
- **Diff for unchanged files** — empty diff. *Mitigation:* collapse
  unchanged hunks.

### Validation

- Run a long task end-to-end and time from "message sent" to "UI
  shows it".
- Hand-verify diff view on 5 completed tasks.

---

## Week 9–10 — Agent Tooling

### Goals

Agents become actors instead of prompts.

### Deliverables

- [ ] **A-9**: Add a `read_file(path)` tool that agents can invoke via
  LangGraph's `ToolNode`. Restrict to `repository_contexts`-known files.
  Wire into Builder, Reviewer, Architect prompts.
- [ ] **A-11**: Add re-review edge in `graph.py`. Cap at 2 retries.
  Wire `max_retries` config.
- [ ] **A-8 stub**: `Sandbox` service that runs pytest in a tmp dir,
  captures exit code + summary. Land with `safe` mode (5s timeout,
  no network).

### Success Metrics

- Builder reads at least one existing file in 80% of eval tasks.
- Re-review loop reduces eval "blocking findings remaining" by ≥30%.
- Sandbox produces pass/fail/skip counts in < 10s for a 100-test
  fixture.

### Risks

- **Tool use hallucination** — agents may call `read_file` on
  non-existent paths. *Mitigation:* tool returns `null` on miss;
  agents learn.
- **Sandbox security** — `safe` mode is not actually safe. *Mitigation:*
  document as best-effort; full sandbox is V1.1.

### Validation

- Eval suite shows ≥20% quality improvement on multi-file tasks.
- Sandbox returns correct exit code on a known-good fixture.

---

## Week 11–12 — GitHub Product Surface v1

### Goals

The GitHub App posts *useful* PR reviews, not just comments.

### Deliverables

- [ ] **G-3**: `Finding` → suggested-code block in PR review comment.
- [ ] **G-4**: One-shot LLM call to produce a top-level summary before
  inline findings.
- [ ] **G-7**: Look up `check_run_id` per `(repo, pr, head_sha)` and
  update rather than recreate.
- [ ] **G-8**: `GET /integrations/github/analytics` route + dashboard
  card on `/analytics`.

### Success Metrics

- 100% of completed reviews include a summary.
- Suggested-code blocks appear in 100% of findings where applicable.
- Zero new check runs per re-review; one updated run.
- Analytics route returns weekly aggregates.

### Risks

- **GitHub API rate limits** — analytics scrape can hit them.
  *Mitigation:* aggregate nightly, not on every page load.
- **Suggested-code formatting** — JSON patch vs raw block.
  *Mitigation:* start with raw ` ```suggestion ` block (simpler).

### Validation

- Install GitHub App on a sandbox repo with 3 PRs.
- Verify summary, suggested blocks, and updated check runs.

---

## External Demo & V0.5 Release (Week 12)

By end of Week 12, ship **V0.5** to a private design partner.

### V0.5 Acceptance Criteria

- [ ] Multi-agent task produces a real diff visible in the UI.
- [ ] Embedding-based memory retrieval is wired.
- [ ] WebSocket streaming on task detail.
- [ ] GitHub PR review posts summary + suggested blocks.
- [ ] Re-review loop runs up to 2 retries.
- [ ] At least 1 decision is captured per passing task.

### Validation Strategy

- 1 design partner runs AgentForge on their own repo for 1 week.
- Daily check-in for first 3 days, then weekly.
- Track: time-to-first-useful-output, number of agent runs per day,
  % of findings the dev accepts.

---

## Risks (90-day level)

### R-90-1 — Engineering capacity

A 2-engineer team for P0 alone is tight. If one engineer leaves or
takes leave, the plan slips by 4 weeks.

**Mitigation:** Cross-train from Day 1. Each engineer shadows the
other's PRs. No single-owner knowledge.

### R-90-2 — LLM provider churn

OpenAI deprecates `text-embedding-3-small` mid-quarter. Anthropic
raises prices. Open-source models close the gap.

**Mitigation:** Provider abstraction already exists in
`core/providers.py`. Budget 3 days for swap-and-test if needed.

### R-90-3 — R-1 turns out bigger than expected

Symbol graphs are famously fiddly. The parser may need tree-sitter
adoption before R-1 works at scale.

**Mitigation:** R-1 ships at a *narrow* scope first (Python only),
then expands. R-3, R-4, R-6 depend on R-1; if R-1 slips, those slip.

### R-90-4 — Eval set doesn't measure what we think

The 5-PR seed set is small. Numbers may move without meaning moving.

**Mitigation:** Curate 25 PRs by Week 8. Document methodology
publicly. Publish precision/recall each release.

### R-90-5 — Design partner adoption fails

The team doesn't actually use AgentForge after Week 12.

**Mitigation:** Have *two* design partners, not one. Run a 30-min
weekly call. If both disengage by Week 10, run a "shadow a developer"
session to find the friction.

---

## What's NOT in 90 Days

- ❌ **Continue provider** (V1.1)
- ❌ **In-app onboarding wizard** (V1.1)
- ❌ **SARIF output** (V1.1)
- ❌ **Required checks support** (V1.2)
- ❌ **Memory decay / consolidation** (V1.2)
- ❌ **Public eval benchmark website** (V1.2)
- ❌ **Decision memory graph view** (V1.2)

These are real, but they don't gate V0.5 / V1.

---

## Definition of Success (90 days)

The 90-day plan succeeds if, by end of Week 12:

1. **V0.5 is in use at a friendly team** that runs ≥5 multi-agent tasks
   per day.
2. **Precision@5 on the eval set improves ≥30%** vs Week 0 baseline.
3. **Agent time-to-first-byte drops from 600ms to 200ms** (WS streaming).
4. **GitHub PR review produces a summary + ≥1 suggested-code block**
   on 100% of installations.
5. **At least one decision** is captured per passing task, queryable
   via `GET /decisions`.
6. **Zero P0 data integrity bugs** (no broken migrations, no schema
   drift, no token leak).

If 5/6 of those are true, V0.5 is real and the team has earned the
right to plan V1.

---

## Honest Assessment

12 weeks is aggressive but feasible. The highest-risk items are R-1
(symbol graph) and A-8 (test sandbox). If either slips by 2 weeks, the
whole schedule compresses.

The lowest-risk, highest-visibility items are DX-7 (WS streaming) and
G-3 (suggested-code blocks). Those should ship *first* to buy political
capital for the harder work.

The single most common failure mode for plans like this is "we built
everything but didn't validate with a real user". The design partner is
not optional. If the partner slips, V0.5 slips.