# AgentForge — Consolidated Findings (2026-06-26)

> Honesty note: the brief asked for "Top 100". Padding a findings list to a round number with
> filler is the kind of vanity metric this audit is supposed to expose. Below are the **real,
> evidence-backed findings** (~60), severity-ranked and deduplicated. Each has file:line. Full
> detail lives in the themed reports.

## P0 — Block multi-tenant production
| # | Finding | Evidence |
|---|---|---|
| 1 | File-download IDOR: any user downloads any project's files | `routes/projects.py:476-505` (`WHERE id=$1 AND project_id=$2`, no ownership) |
| 2 | Same missing-ownership gap on file update/delete queries | `routes/projects.py:442,460,467` |
| 3 | Redis required at boot, absent from compose → app won't start cleanly | `app/main.py:57`, `docker-compose.yml` (no redis svc) |

## P1 — Fix before GA
| # | Finding | Evidence |
|---|---|---|
| 4 | Task-creation IDOR: task can target a team you don't own | `routes/tasks.py:54-71` |
| 5 | No refresh-token revocation/rotation; no `/logout` | `app/auth.py:59,88`; `routes/auth.py` `/refresh` |
| 6 | Prompt injection: user task + uploaded file content rendered into system prompt | `agents/nodes/team_lead_node.py:24`, `builder_node.py:24` |
| 7 | JWT refresh secret falls back to access secret; literal dev fallback reachable when auth off | `app/auth.py:33-38` |
| 8 | Ephemeral encryption key path → BYOK keys lost on restart | `core/encryption.py:14-24` |
| 9 | CORS `allow_methods=["*"]`,`allow_headers=["*"]`,`credentials=True` | `app/main.py:172-178` |
| 10 | Brute-force lockout keyed `email:ip` → IP-rotation bypass | `routes/auth.py:36-38` |
| 11 | In-memory rate-limit/review/metrics break horizontal scaling | `core/redis.py:60,117,165`; `core/observability.py:51` |
| 12 | Task tracker per-instance; `/metrics` active count per-process | `core/task_tracker.py:14-15` |
| 13 | Blocking file write in async upload | `routes/projects.py:275-276` |
| 14 | Blocking `path.read_text()` in async parse path | `app/file_parser.py:363` |
| 15 | Migrations run on boot with no advisory lock → multi-instance race | `app/main.py:54` |
| 16 | Missing index `tasks(created_by)` (filtered hot path) | `routes/tasks.py:91`; `migrations/001` |
| 17 | Missing index `executions(created_by)` | `migrations/010`; `routes/analytics.py:43,93,125` |
| 18 | Memory read by only 1 of 8 agents (write-mostly) | `team_lead.jinja2:10-14` vs other prompts |
| 19 | Aggregator falls back to substring `"fail"` verdict | `agents/nodes/aggregator_node.py:71-96` |
| 20 | No build↔review loop; 4 reviewers see identical input (~4× tokens, no specialization) | `agents/graph.py:29-68` |
| 21 | Frontend tokens in `localStorage` (XSS → theft) | `components/auth/auth-context.tsx:39-41` |
| 22 | No client route protection / no redirect on final 401 | `lib/api.ts`; all `app/*/page.tsx` |
| 23 | "40% more bugs" is hardcoded, never computed | `BENCHMARK_SHOWCASE_PRD.md` |
| 24 | No labeled benchmark/quality measurement exists | `benchmark_simplified.py:~213`, `benchmark_scientific.py` (abandoned) |
| 25 | `/projects` and `/context` route layers have zero route-level tests | `tests/` (no `test_projects.py`/`test_context.py`) |
| 26 | CI security/lint gates non-blocking (`|| true`, `continue-on-error`) | `.github/workflows/ci.yml:~41,116,166` |

## P2 — Hardening / quality
| # | Finding | Evidence |
|---|---|---|
| 27 | Login timing oracle (bcrypt only on valid user) | `routes/auth.py:53-65` |
| 28 | `/memories` POST has no Pydantic schema | `routes/memories.py:79-99` |
| 29 | Broad `except Exception` masks insert errors as 409 | `routes/projects.py:210-211` |
| 30 | File parser swallows all read errors silently | `file_parser.py:366-367` |
| 31 | `verify_password` swallows exceptions unlogged | `app/auth.py:45-49` |
| 32 | Zip extraction keeps dir components; symlinks not disabled | `routes/projects.py:343-356` |
| 33 | Uploads stored under app dir; FileResponse bypasses cache headers | `routes/projects.py:476-505`; `main.py:156-163` |
| 34 | Security-critical deps unpinned (`cryptography/bcrypt/PyJWT >=`) | `requirements.txt` |
| 35 | No Python type-checking in CI (no mypy/pyright) | `.github/workflows/ci.yml` |
| 36 | In-memory metrics capped at 1000, lost on restart, per-process | `core/observability.py:51,63-64` |
| 37 | No tracing (no OpenTelemetry) | `core/observability.py` |
| 38 | Graceful-shutdown 30s vs Docker 10s SIGTERM → tasks SIGKILLed | `main.py:69` |
| 39 | No service/repository layer; business logic in routes | `routes/projects.py:511-581` |
| 40 | Memory WHERE built by string join (values still param'd) | `memory_service.py:~98-104` |
| 41 | Memory retrieval is keyword ILIKE, no embeddings/semantic rank | `memory_service.py:112-162` |
| 42 | `tester` agent proposes tests but never runs them | `agents/nodes/tester_node.py` |
| 43 | reviewer/security/architect semantic overlap | `agents/prompts/{reviewer,security,architect}.jinja2` |
| 44 | Thin prompts: no few-shot, no severity rubric | `agents/prompts/*.jinja2` |
| 45 | Fire-and-forget context parse, no status callback on failure | `routes/projects.py:577-579` |
| 46 | Demo user seeded with SHA-256 hash (mitigated by mig 013 if run) | `migrations/005:8` |
| 47 | Dead components: `status-dot.tsx`, `ui/skeleton.tsx` | `apps/web/components/` |
| 48 | Quick-Review UI duplicated 3× | `page.tsx:49-114`, `dashboard:21-96`, `review:14-78` |
| 49 | Every page `"use client"`; useEffect fetching, no SWR/react-query | `app/*/page.tsx:1` |
| 50 | Icon-only buttons lack aria-labels; no modal focus trap | `sidebar.tsx:96`, `topbar.tsx:96` |
| 51 | No timeout/cancel UI on task polling | `tasks/[id]/page.tsx` |
| 52 | Review history browser-local only (no retention) | `page.tsx:87-97` |
| 53 | `/demo` is a client-side animation, not the real pipeline | `lib/demo-data.ts` |
| 54 | No failure-path integration tests (LLM timeout/DB outage/5xx) | `tests/` |
| 55 | Weak/vacuous tests (`test_health` status-only; `test_providers` `except: pass`) | `tests/test_health.py`, `tests/test_providers.py` |
| 56 | Coverage computed but not enforced | `pyproject.toml`; CI |
| 57 | `orchestrator.py` UPDATE/DELETE scoped by task_id only (defense-in-depth) | `agents/orchestrator.py:79-194` |
| 58 | 522MB `AgentForge.zip` committed in working tree (repo hygiene) | repo root |
| 59 | ~40 overlapping self-audit `.md` files in root (noise/credibility) | repo root |
| 60 | Git remote points at unrelated `JAVA.git`; repo not properly initialized | `git remote -v` |

## Corrections to first-pass agent claims (kept honest)
- **Not** a committed-secret P0: `.env` is gitignored (`apps/api/.gitignore:15-16`) and
  `config.validate()` enforces JWT secret presence/length when auth is on (`core/config.py:89-110`).
- **`alg=none` is not currently exploitable:** PyJWT≥2 rejects it and decode pins `["HS256"]`
  (`auth.py:69,98`). Risk is theoretical, downgraded to dependency-pinning hygiene.
- SQL injection: **none found** — all values are parameterized.
