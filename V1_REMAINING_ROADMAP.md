# V1 Remaining Roadmap

**Scope:** Everything that must be true for AgentForge V1 to be a
*credible, daily-use, multi-agent software development platform* —
distinct from a polished demo. Sequenced by leverage (user value per
engineering week) and dependency (what blocks what).

**Verdict:** V1 needs **four P0 layers** (repo intelligence, agent
collaboration, dev experience, embeddings) plus **one P1 layer** (GitHub
product surface) plus **one P2 layer** (memory graph). Total: 22–28
weeks of focused work for a 2–3 person team. After that, AgentForge
stops being "an AI tool that runs" and starts being "a platform teams
plan around".

---

## Priority Definitions

- **P0** — V1 cannot ship without this. Missing these makes AgentForge
  a demo, not a product.
- **P1** — V1 ships without this but is uncompetitive without it.
- **P2** — V1+ differentiation. Worth doing once P0/P1 are stable.

---

## P0 — Required for V1 Launch

### Layer 1 — Repository Intelligence Engine (R-1 through R-6)

The single highest-leverage investment. Today the schema exists; the
engine doesn't. Without this, every agent review is "guess the file from
its name".

| ID | Title | Effort | Dependency | User value |
|---|---|---|---|---|
| R-1 | Add `code_edges` table + recursive CTE reachability | 2 weeks | none | Enables blast-radius, call graph, cross-file reasoning |
| R-2 | `POST /repo/explain` — Architect over the whole repo | 1 week | R-1 | First product surface for "explain my codebase" |
| R-3 | Architectural pattern detection | 1 week | R-1 | Lets agents reason about layering, not just files |
| R-4 | Risky-file scoring (PageRank over symbol graph) | 1 week | R-1 | Reviewer can prioritize findings |
| R-5 | Incremental re-indexing (hash + mtime cache) | 1 week | none | Required for repos > 5k files |
| R-6 | Git blame + CODEOWNERS consumption | 1 week | none | Builder follows owner style; review routes to owners |

**Total: 6–7 weeks.**

### Layer 2 — Agent Collaboration Core (A-7 through A-11)

Make the existing agents actually collaborate instead of perform
sequential monologues.

| ID | Title | Effort | Dependency | User value |
|---|---|---|---|---|
| A-7 | Wire review feedback to Builder | 2 days | none | Findings become actionable — Builder revises |
| A-8 | Run Tester-emitted tests in sandbox | 2 weeks | none | "Pass / fail / 73% covered" instead of "here are some tests" |
| A-9 | File-reading tools for agents | 2 weeks | none | Builder stops hallucinating files |
| A-10 | Validate every agent output (Pydantic + retry) | 1 week | none | Removes ~30% of garbage downstream |
| A-11 | Re-review loop with cost cap | 1 week | A-7, A-10 | Multi-pass quality without explosion |

**Total: 6–7 weeks.** Can run in parallel with Layer 1.

### Layer 3 — Memory & Embeddings (M-1 through M-3)

The single most embarrassing gap. Without embeddings, AgentForge is the
only AI dev tool in 2026 that retrieves by keyword.

| ID | Title | Effort | Dependency | User value |
|---|---|---|---|---|
| M-1 | Add `embedding vector(1536)` column + HNSW index | 1 week | pgvector enabled | Synonym/paraphrase retrieval |
| M-2 | `decisions` table + ADR route | 2 weeks | none | "Why did we use Postgres" becomes queryable |
| M-3 | `features` table + feature-history route | 1 week | none | "What did this team ship in Q2?" |

**Total: 4 weeks.** Depends on Layer 1 partially (uses symbol graph for
memory linkage).

### Layer 4 — Developer Experience Foundations (DX-7, DX-8, DX-9)

The three changes that make the product *feel* different from a demo.

| ID | Title | Effort | Dependency | User value |
|---|---|---|---|---|
| DX-7 | WebSocket streaming on task detail | 1 week | backend WS exists | "Why is this slow?" goes away |
| DX-8 | Generate TS + Python SDK from OpenAPI | 2 weeks | none | Maintenance + new surfaces (Continue provider, etc.) |
| DX-9 | Real diff view on task delivery | 2 weeks | R-1 | "What changed?" goes from mystery to obvious |

**Total: 5 weeks.** Can run in parallel with all other P0.

### P0 Subtotal: 21–23 weeks (with 2 engineers in parallel: ~12 weeks)

---

## P1 — V1 Launch Quality Bar

These define the difference between "credible V1" and "credible V1 that
people recommend".

### Layer 5 — GitHub Product Surface (G-1, G-2, G-3, G-4, G-5, G-7, G-8, G-10)

| ID | Title | Effort | Dependency | User value |
|---|---|---|---|---|
| G-1 | Diff-aware context (pull full files for the PR) | 2 weeks | R-1 | Findings reference real symbols |
| G-2 | `pull_request_review_comment` + `issue_comment` handlers | 1 week | none | Developer can talk to the bot |
| G-3 | Suggested-code blocks | 1 week | none | "Apply fix in one click" — biggest UX win |
| G-4 | PR summary before findings | 1 week | none | Review readable on mobile |
| G-5 | `/agentforge` slash command + conversation | 2 weeks | G-2 | Bot answers follow-up questions |
| G-7 | Update existing check run, not new ones | 1 week | none | No more stale check runs |
| G-8 | Review analytics route + dashboard card | 1 week | none | Teams see ROI |
| G-10 | Web-side OAuth install flow | 2 weeks | none | Install in one click |

**Total: 10–11 weeks.** Some can parallelize.

### Layer 6 — DX Iteration (DX-10 through DX-14)

| ID | Title | Effort | Dependency |
|---|---|---|---|
| DX-10 | `agentforge init` + `task --watch` | 1 week | none |
| DX-11 | SARIF output from CLI | 1 week | none |
| DX-12 | In-app onboarding wizard | 2 weeks | none |
| DX-13 | Apply-suggestions (web + CLI) | 1 week | none |
| DX-14 | Pagination + filtering on list endpoints | 1 week | DX-8 |

**Total: 6 weeks.**

### Layer 7 — Eval & Observability (V-1 through V-4)

This is the layer that makes AgentForge *believable*. Without it, every
claim is unverified.

| ID | Title | Effort | Dependency |
|---|---|---|---|
| V-1 | Public benchmark suite (50 real PRs) | 2 weeks | A-10, M-1 |
| V-2 | Per-agent latency/cost dashboard | 1 week | none |
| V-3 | Eval-driven prompt regression (CI gate) | 2 weeks | V-1 |
| V-4 | Eval harness for acceptance rate | 1 week | V-1 |

**Total: 6 weeks.**

### P1 Subtotal: 22–23 weeks (parallel: ~10–12 weeks)

---

## P2 — V1+ Differentiation

These define what AgentForge is in 12+ months.

### Layer 8 — Memory Graph (M-4 through M-8)

| ID | Title | Effort |
|---|---|---|
| M-4 | Refactoring memory (typed schema in `agent_memories`) | 1 week |
| M-5 | Mid-graph retrieval helper | 2 weeks |
| M-6 | Team-scope memory + share route | 1 week |
| M-7 | Memory decay background job | 1 week |
| M-8 | Memory viewer with semantic search | 1 week |

**Total: 6 weeks.**

### Layer 9 — GitHub Enterprise (G-11, G-12)

| ID | Title | Effort |
|---|---|---|
| G-11 | Required check support | 1 week |
| G-12 | CODEOWNERS-aware review routing | 1 week |

### Layer 10 — Agent Reasoning (A-12 through A-15)

| ID | Title | Effort |
|---|---|---|
| A-12 | SAST + secrets integration in Security agent | 2 weeks |
| A-13 | Real line numbers in findings | 1 week |
| A-14 | Structured inter-agent protocol (`AgentMessage`) | 2 weeks |
| A-15 | Architect whole-repo mode (covered by R-2 above) | — |

### P2 Subtotal: ~13 weeks.

---

## Effort & Sequencing Summary

| Phase | Wall-clock (2 engineers, parallel) | Wall-clock (1 engineer, sequential) |
|---|---|---|
| P0 | 11–12 weeks | 21–23 weeks |
| P1 | 10–12 weeks | 22–23 weeks |
| P2 | 6–7 weeks | 13 weeks |
| **Total** | **27–31 weeks** | **56–59 weeks** |

For a team of 2 engineers working in parallel, V1 ships in **~7 months**.
For a solo engineer, V1 ships in **~14 months**. For a team of 3–4,
V1 ships in **~5 months** with room for eval hardening.

---

## What V1 Looks Like When Done

A developer can:

1. **Connect a repo in 60 seconds** via GitHub OAuth (G-10).
2. **See a layered architecture summary** of the codebase within 30s
   (R-2).
3. **Open a PR** and have AgentForge post a **summary + suggested-code
   findings** within 60s (G-3, G-4).
4. **Reply to a finding** with "@agentforge why?" and get a contextual
   answer (G-5).
5. **Run a multi-agent task** from the web app *or* the CLI, **streamed
   live**, and see a **real diff** at the end (DX-7, DX-9).
6. **Accept / reject findings** and have the next review *not repeat
   rejected ones* (W-2).
7. **Search memory** semantically — "what did we decide about
   caching?" — and get a relevance-ordered set with links to PRs
   (M-1, M-8).
8. **Run a benchmark** against the public eval set and see AgentForge's
   precision/recall vs prior versions (V-1).

That is V1. None of these are impossible. All of them are scoped.

---

## Risks and Mitigations

### Risk 1 — Repository intelligence blows up

Recursive CTEs over a 100k-file repo can be slow. Mitigation: HNSW
index, materialized views, debounce re-indexing.

### Risk 2 — Multi-agent costs spiral

Each task today is ~3–6 LLM calls. Adding the re-review loop and
mid-graph retrieval could 3–5x cost. Mitigation: cost cap per task
(`max_cost_usd`), aggressive caching, retrieval result reuse.

### Risk 3 — Sandbox for Tester is heavy

Pyodide / Docker / VM-based test runners are non-trivial infra. Fallback:
shell out to pytest in a tmp dir with strict timeouts, capture exit code
and stdout. Imperfect but cheap.

### Risk 4 — Eval set bias

50 hand-picked PRs will overfit. Mitigation: rotate eval sets quarterly,
include adversarial (trick-finding) PRs, publish methodology.

### Risk 5 — Feature creep

The P0 surface is large. The P1 surface is larger. Mitigation: ship
Layer 1 + Layer 2 + DX-7 as the *minimum V1*; defer everything else to
V1.1.

---

## Honest Assessment

The roadmap is honest. It is also big. The single most common failure
mode for a product like this is "build everything for everyone". The
recommended path is:

- **Weeks 1–12:** P0 only. Ship a V0.5 (release-early) at week 6, V1
  beta at week 12.
- **Weeks 13–24:** P1. V1 GA at week 24.
- **Weeks 25+:** P2.

Anything else is feature creep dressed as strategy.