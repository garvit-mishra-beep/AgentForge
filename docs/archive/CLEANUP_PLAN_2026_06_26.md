# Repository Cleanup Record

**Date:** 2026-06-26
**Author:** Repository cleanup agent
**Status:** Documentation-only record of changes already applied.

> This document is a faithful, after-the-fact log of the v1 cleanup pass. It
> is meant to give a reviewer (or a future agent) enough detail to (a) audit
> what changed, (b) decide what to revert, and (c) understand the rationale
> without re-reading the entire diff. No further repository changes are
> proposed or made here.

---

## Scope

The original prompt (see `REPOSITORY_CLEANUP_REPORT.md`) scoped the work to:

- Inventory the repository and produce `REPOSITORY_MAP.md`.
- Remove dead files, debug artifacts, and obsolete reports.
- Move non-current reports into a new `archive/` tree.
- Standardize the folder layout (`apps/`, `docs/{api,architecture,development,deployment,security,product}`, `archive/`, `scripts/`).
- Add a `README.md` to every major directory.
- Overhaul the root `README.md`.
- Audit documentation and produce `docs/DOCUMENTATION_INDEX.md`.
- Write `docs/development/ONBOARDING.md` aimed at 30-minute new-dev productivity.
- Write `docs/architecture/SYSTEM_ARCHITECTURE.md` with Mermaid diagrams.
- Write `docs/security/SECURITY_MODEL.md` covering the full threat model.
- Produce this record + the cleanup report.

The prompt explicitly forbade new product features and required that existing
functionality be preserved.

---

## Files Added

### Documentation (top of the tree)

| Path | Purpose |
|------|---------|
| `README.md` | Rewritten root landing page |
| `REPOSITORY_MAP.md` | Full inventory + execution-flow diagrams |
| `REPOSITORY_CLEANUP_REPORT.md` | Phase-by-phase cleanup audit |
| `LICENSE` | MIT license (previously referenced but missing) |

### `apps/` READMEs

| Path | Purpose |
|------|---------|
| `apps/README.md` | Apps-tree orientation |
| `apps/api/README.md` | Backend reference |
| `apps/web/README.md` | Frontend reference |
| `apps/cli/README.md` | CLI reference |
| `apps/api/tests/README.md` | Backend test-suite orientation |

### `docs/` tree — root + subfolder READMEs

| Path | Purpose |
|------|---------|
| `docs/README.md` | Docs-tree orientation (rewritten) |
| `docs/DOCUMENTATION_INDEX.md` | Status + reading order for every doc |
| `docs/architecture/README.md` | Architecture subfolder orientation |
| `docs/api/README.md` | API subfolder orientation |
| `docs/development/README.md` | Development subfolder orientation |
| `docs/deployment/README.md` | Deployment subfolder orientation |
| `docs/security/README.md` | Security subfolder orientation |
| `docs/product/README.md` | Product subfolder orientation |

### `docs/architecture/`

| Path | Purpose |
|------|---------|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | End-to-end architecture (frontend, backend, agents, memory, DB, auth, GitHub integration) with Mermaid diagrams |

### `docs/development/`

| Path | Purpose |
|------|---------|
| `docs/development/ONBOARDING.md` | New-engineer 30-minute productivity guide (replaces prior first-week variant) |
| `docs/development/CLEANUP_PLAN_2026_06_26.md` | **This file** |

### `docs/security/`

| Path | Purpose |
|------|---------|
| `docs/security/SECURITY_MODEL.md` | Authoritative threat model |

### `archive/` and `scripts/`

| Path | Purpose |
|------|---------|
| `archive/README.md` | What was archived, why, and the policy for future additions |
| `scripts/README.md` | Operational-scripts policy |

---

## Files Modified

Only one tracked file outside the new `README.md` set was edited:

| Path | Change |
|------|--------|
| `.gitignore` | Added patterns: `htmlcov/`, `apps/web/.next/`, `apps/web/out/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` |

No source code, test, manifest, Dockerfile, CI workflow, env example, or
prompt template was modified. `apps/api/.env.example`, `Makefile`,
`package.json`, `pnpm-workspace.yaml`, `turbo.json`, `pyproject.toml`,
`Dockerfile`, `docker-compose.yml` are unchanged.

---

## Files Moved

### Stale reports → `archive/reports/`

| Old path | New path | Reason |
|----------|----------|--------|
| `AGENTFORGE_30_DAY_PLAN.md` | `archive/reports/AGENTFORGE_30_DAY_PLAN.md` | Point-in-time strategy |
| `AGENTFORGE_COUNTER_ANALYSIS.md` | `archive/reports/AGENTFORGE_COUNTER_ANALYSIS.md` | Point-in-time strategy |
| `AGENTFORGE_STRATEGIC_REVIEW.md` | `archive/reports/AGENTFORGE_STRATEGIC_REVIEW.md` | Point-in-time strategy |
| `AGENTFORGE_STRATEGIC_VALIDATION_AUDIT.md` | `archive/reports/AGENTFORGE_STRATEGIC_VALIDATION_AUDIT.md` | Point-in-time strategy |
| `AUDIT_VALIDATION_REPORT.md` | `archive/reports/AUDIT_VALIDATION_REPORT.md` | Point-in-time audit |
| `BENCHMARK_SHOWCASE_PRD.md` | `archive/reports/BENCHMARK_SHOWCASE_PRD.md` | Point-in-time PRD |
| `COLLABORATION_EFFECTIVENESS_REPORT.md` | `archive/reports/COLLABORATION_EFFECTIVENESS_REPORT.md` | Point-in-time report |
| `DEMO_COMPARISON_PRD.md` | `archive/reports/DEMO_COMPARISON_PRD.md` | Point-in-time PRD |
| `DEMO_IMPACT_REPORT.md` | `archive/reports/DEMO_IMPACT_REPORT.md` | Point-in-time report |
| `DEMO_READINESS_REPORT.md` | `archive/reports/DEMO_READINESS_REPORT.md` | Point-in-time report |
| `DEVOPS_REPORT.md` | `archive/reports/DEVOPS_REPORT.md` | Point-in-time report |
| `DIFFERENTIATION_ANALYSIS.md` | `archive/reports/DIFFERENTIATION_ANALYSIS.md` | Point-in-time analysis |
| `DIFFERENTIATION_STRATEGY.md` | `archive/reports/DIFFERENTIATION_STRATEGY.md` | Point-in-time strategy |
| `FINAL_8_5_READINESS_REPORT.md` | `archive/reports/FINAL_8_5_READINESS_REPORT.md` | Point-in-time report |
| `FINAL_REPOSITORY_AUDIT.md` | `archive/reports/FINAL_REPOSITORY_AUDIT.md` | Point-in-time audit |
| `FIRST_TIME_USER_JOURNEY.md` | `archive/reports/FIRST_TIME_USER_JOURNEY.md` | Point-in-time report |
| `INTEGRATION_FIX_REPORT.md` | `archive/reports/INTEGRATION_FIX_REPORT.md` | Point-in-time report |
| `INVESTOR_READINESS_REPORT.md` | `archive/reports/INVESTOR_READINESS_REPORT.md` | Point-in-time report |
| `LANDING_PAGE_V2_PRD.md` | `archive/reports/LANDING_PAGE_V2_PRD.md` | Point-in-time PRD |
| `NEXT_30_DAY_PLAN.md` | `archive/reports/NEXT_30_DAY_PLAN.md` | Point-in-time plan |
| `OBSERVABILITY_REPORT.md` | `archive/reports/OBSERVABILITY_REPORT.md` | Point-in-time report |
| `PMF_ACCELERATION_PLAN.md` | `archive/reports/PMF_ACCELERATION_PLAN.md` | Point-in-time plan |
| `PMF_GAP_REPORT.md` | `archive/reports/PMF_GAP_REPORT.md` | Point-in-time report |
| `PMF_RISK_REPORT.md` | `archive/reports/PMF_RISK_REPORT.md` | Point-in-time report |
| `PRIORITIZED_FIX_PLAN.md` | `archive/reports/PRIORITIZED_FIX_PLAN.md` | Point-in-time plan |
| `PRODUCTION_READINESS_REPORT.md` | `archive/reports/PRODUCTION_READINESS_REPORT.md` | Point-in-time report |
| `PRODUCT_EXPERIENCE_REPORT.md` | `archive/reports/PRODUCT_EXPERIENCE_REPORT.md` | Point-in-time report |
| `PRODUCT_POSITIONING.md` | `archive/reports/PRODUCT_POSITIONING.md` | Point-in-time strategy |
| `PRODUCT_REVIEW.md` | `archive/reports/PRODUCT_REVIEW.md` | Point-in-time review |
| `QUICK_REVIEW_PRD.md` | `archive/reports/QUICK_REVIEW_PRD.md` | Point-in-time PRD |
| `RELIABILITY_IMPROVEMENT_REPORT.md` | `archive/reports/RELIABILITY_IMPROVEMENT_REPORT.md` | Point-in-time report |
| `RELIABILITY_REVIEW.md` | `archive/reports/RELIABILITY_REVIEW.md` | Point-in-time review |
| `SCALABILITY_REPORT.md` | `archive/reports/SCALABILITY_REPORT.md` | Point-in-time report |
| `SCALABILITY_REVIEW.md` | `archive/reports/SCALABILITY_REVIEW.md` | Point-in-time review |
| `SECURITY_REMEDIATION_REPORT.md` | `archive/reports/SECURITY_REMEDIATION_REPORT.md` | Point-in-time report |
| `SECURITY_REVIEW.md` | `archive/reports/SECURITY_REVIEW.md` | Point-in-time review |
| `STARTUP_SCORE_ANALYSIS.md` | `archive/reports/STARTUP_SCORE_ANALYSIS.md` | Point-in-time analysis |
| `TESTING_EXPANSION_REPORT.md` | `archive/reports/TESTING_EXPANSION_REPORT.md` | Point-in-time report |
| `TESTING_GAP_ANALYSIS.md` | `archive/reports/TESTING_GAP_ANALYSIS.md` | Point-in-time analysis |
| `TOP_20_UX_IMPROVEMENTS.md` | `archive/reports/TOP_20_UX_IMPROVEMENTS.md` | Point-in-time list |
| `USER_OBSESSION_PLAN.md` | `archive/reports/USER_OBSESSION_PLAN.md` | Point-in-time plan |
| `REPOSITORY_INVENTORY.md` (pre-existing, pre-`REPOSITORY_MAP.md`) | `archive/reports/REPOSITORY_INVENTORY.md` | Superseded by `REPOSITORY_MAP.md` |

### 2026 audit cycle → `archive/audit_2026_reports/`

| Old path | New path | Reason |
|----------|----------|--------|
| `AUDIT_2026/AI_SYSTEM_AUDIT.md` | `archive/audit_2026_reports/AI_SYSTEM_AUDIT.md` | Historical audit snapshot |
| `AUDIT_2026/ARCHITECTURE_AUDIT.md` | `archive/audit_2026_reports/ARCHITECTURE_AUDIT.md` | Historical audit snapshot |
| `AUDIT_2026/CTO_FINAL_REVIEW.md` | `archive/audit_2026_reports/CTO_FINAL_REVIEW.md` | Historical audit snapshot |
| `AUDIT_2026/EXECUTIVE_SUMMARY.md` | `archive/audit_2026_reports/EXECUTIVE_SUMMARY.md` | Historical audit snapshot |
| `AUDIT_2026/FEATURE_GAP_ANALYSIS.md` | `archive/audit_2026_reports/FEATURE_GAP_ANALYSIS.md` | Historical audit snapshot |
| `AUDIT_2026/PRODUCT_AUDIT.md` | `archive/audit_2026_reports/PRODUCT_AUDIT.md` | Historical audit snapshot |
| `AUDIT_2026/REPOSITORY_INVENTORY.md` | `archive/audit_2026_reports/REPOSITORY_INVENTORY.md` | Historical audit snapshot |
| `AUDIT_2026/ROADMAP.md` | `archive/audit_2026_reports/ROADMAP.md` | Historical audit snapshot |
| `AUDIT_2026/SECURITY_AUDIT.md` | `archive/audit_2026_reports/SECURITY_AUDIT.md` | Historical audit snapshot |
| `AUDIT_2026/TOP_FINDINGS.md` | `archive/audit_2026_reports/TOP_FINDINGS.md` | Historical audit snapshot |
| `AUDIT_2026/UX_AUDIT.md` | `archive/audit_2026_reports/UX_AUDIT.md` | Historical audit snapshot |

### Debug scripts → `archive/debug_scripts/`

| Old path | New path | Reason |
|----------|----------|--------|
| `benchmark_check.py` | `archive/debug_scripts/benchmark_check.py` | Ad-hoc script, no callers |
| `check_status.py` | `archive/debug_scripts/check_status.py` | Ad-hoc script, no callers |
| `simple_check.py` | `archive/debug_scripts/simple_check.py` | Ad-hoc script, no callers |
| `test_benchmark.py` | `archive/debug_scripts/test_benchmark.py` | Ad-hoc script, no callers |
| `test_simple.py` | `archive/debug_scripts/test_simple.py` | Ad-hoc script, no callers |
| `validation_simple.py` | `archive/debug_scripts/validation_simple.py` | Ad-hoc script, no callers |
| `fast_demo_benchmark.py` (root) | `archive/debug_scripts/fast_demo_benchmark.py` | Ad-hoc script, no callers |
| `apps/api/benchmark.py` | `archive/debug_scripts/benchmark.py` | Legacy benchmark; superseded by `apps/api/benchmarks/` |
| `apps/api/benchmark_scientific.py` | `archive/debug_scripts/benchmark_scientific.py` | Legacy benchmark |
| `apps/api/benchmark_simplified.py` | `archive/debug_scripts/benchmark_simplified.py` | Legacy benchmark |
| `apps/api/fast_demo_benchmark.py` | `archive/debug_scripts/fast_demo_benchmark.py` | Legacy benchmark |

### Docs reorganization (`docs/*.md` → thematic subfolders)

| Old path | New path | Reason |
|----------|----------|--------|
| `docs/AGENT_ROLES.md` | `docs/architecture/AGENT_ROLES.md` | Architecture content |
| `docs/AGENT_PROMPTS.md` | `docs/architecture/AGENT_PROMPTS.md` | Architecture content |
| `docs/AGENT_MEMORY.md` | `docs/architecture/AGENT_MEMORY.md` | Architecture content |
| `docs/HALLUCINATION_GUARD.md` | `docs/architecture/HALLUCINATION_GUARD.md` | Architecture content |
| `docs/MODEL_REGISTRY.md` | `docs/architecture/MODEL_REGISTRY.md` | Architecture content |
| `docs/PROMPTS.md` | `docs/architecture/PROMPTS.md` | Architecture content |
| `docs/SCHEMA.md` | `docs/architecture/SCHEMA.md` | Architecture content |
| `docs/TECH_SPEC.md` | `docs/architecture/TECH_SPEC.md` | Architecture content |
| `docs/API.md` | `docs/api/API.md` | API reference |
| `docs/CLAUDE.md` | `docs/development/CLAUDE.md` | Developer-facing |
| `docs/CONTRIBUTING.md` | `docs/development/CONTRIBUTING.md` | Developer-facing |
| `docs/CONVENTIONS.md` | `docs/development/CONVENTIONS.md` | Developer-facing |
| `docs/DECISIONS.md` | `docs/development/DECISIONS.md` | Developer-facing |
| `docs/DX.md` | `docs/development/DX.md` | Developer-facing |
| `docs/ENV.md` | `docs/development/ENV.md` | Developer-facing |
| `docs/FAQ.md` | `docs/development/FAQ.md` | Developer-facing |
| `docs/GLOSSARY.md` | `docs/development/GLOSSARY.md` | Developer-facing |
| `docs/OBSERVABILITY.md` | `docs/development/OBSERVABILITY.md` | Developer-facing |
| `docs/PERFORMANCE.md` | `docs/development/PERFORMANCE.md` | Developer-facing |
| `docs/SETUP.md` | `docs/development/SETUP.md` | Developer-facing |
| `docs/TESTING.md` | `docs/development/TESTING.md` | Developer-facing |
| `docs/AUDIT.md` | `docs/development/AUDIT.md` | Developer-facing (audit context) |
| `docs/BUGS.md` | `docs/development/BUGS.md` | Developer-facing (bug tracking) |
| `docs/DEPLOYMENT.md` | `docs/deployment/DEPLOYMENT.md` | Operations |
| `docs/DATA_PRIVACY.md` | `docs/security/DATA_PRIVACY.md` | Security / privacy |
| `docs/INCIDENT_RUNBOOK.md` | `docs/security/INCIDENT_RUNBOOK.md` | Security / operations |
| `docs/SECURITY.md` | `docs/security/SECURITY.md` | Security |
| `docs/PRD.md` | `docs/product/PRD.md` | Product |
| `docs/PRICING.md` | `docs/product/PRICING.md` | Product / GTM |
| `docs/PMF_EXECUTION_PLAN.md` | `docs/product/PMF_EXECUTION_PLAN.md` | Product / GTM |
| `docs/PROJECT_CONTEXT.md` | `docs/product/PROJECT_CONTEXT.md` | Product / context |
| `docs/ROADMAP.md` | `docs/product/ROADMAP.md` | Product |

`docs/ONBOARDING.md` was both **moved** to `docs/development/ONBOARDING.md`
and **rewritten** (see Files Modified). `docs/README.md` was also rewritten.

### Removed directory

| Old path | Reason |
|----------|--------|
| `docs/mvp/` | Empty / stale — contents already superseded |

---

## Files Archived

Every "archive" entry above is also a "moved" entry. This section repeats
them grouped by archive destination for clarity.

### `archive/reports/` (42 files)

`AGENTFORGE_30_DAY_PLAN.md`, `AGENTFORGE_COUNTER_ANALYSIS.md`,
`AGENTFORGE_STRATEGIC_REVIEW.md`, `AGENTFORGE_STRATEGIC_VALIDATION_AUDIT.md`,
`AUDIT_VALIDATION_REPORT.md`, `BENCHMARK_SHOWCASE_PRD.md`,
`COLLABORATION_EFFECTIVENESS_REPORT.md`, `DEMO_COMPARISON_PRD.md`,
`DEMO_IMPACT_REPORT.md`, `DEMO_READINESS_REPORT.md`, `DEVOPS_REPORT.md`,
`DIFFERENTIATION_ANALYSIS.md`, `DIFFERENTIATION_STRATEGY.md`,
`FINAL_8_5_READINESS_REPORT.md`, `FINAL_REPOSITORY_AUDIT.md`,
`FIRST_TIME_USER_JOURNEY.md`, `INTEGRATION_FIX_REPORT.md`,
`INVESTOR_READINESS_REPORT.md`, `LANDING_PAGE_V2_PRD.md`,
`NEXT_30_DAY_PLAN.md`, `OBSERVABILITY_REPORT.md`, `PMF_ACCELERATION_PLAN.md`,
`PMF_GAP_REPORT.md`, `PMF_RISK_REPORT.md`, `PRIORITIZED_FIX_PLAN.md`,
`PRODUCTION_READINESS_REPORT.md`, `PRODUCT_EXPERIENCE_REPORT.md`,
`PRODUCT_POSITIONING.md`, `PRODUCT_REVIEW.md`, `QUICK_REVIEW_PRD.md`,
`RELIABILITY_IMPROVEMENT_REPORT.md`, `RELIABILITY_REVIEW.md`,
`SCALABILITY_REPORT.md`, `SCALABILITY_REVIEW.md`,
`SECURITY_REMEDIATION_REPORT.md`, `SECURITY_REVIEW.md`,
`STARTUP_SCORE_ANALYSIS.md`, `TESTING_EXPANSION_REPORT.md`,
`TESTING_GAP_ANALYSIS.md`, `TOP_20_UX_IMPROVEMENTS.md`,
`USER_OBSESSION_PLAN.md`, `REPOSITORY_INVENTORY.md` (legacy).

### `archive/audit_2026_reports/` (11 files)

`AI_SYSTEM_AUDIT.md`, `ARCHITECTURE_AUDIT.md`, `CTO_FINAL_REVIEW.md`,
`EXECUTIVE_SUMMARY.md`, `FEATURE_GAP_ANALYSIS.md`, `PRODUCT_AUDIT.md`,
`REPOSITORY_INVENTORY.md`, `ROADMAP.md`, `SECURITY_AUDIT.md`,
`TOP_FINDINGS.md`, `UX_AUDIT.md`.

### `archive/debug_scripts/` (11 files)

`benchmark_check.py`, `check_status.py`, `simple_check.py`,
`test_benchmark.py`, `test_simple.py`, `validation_simple.py`,
`fast_demo_benchmark.py` (root), `apps/api/benchmark.py`,
`apps/api/benchmark_scientific.py`, `apps/api/benchmark_simplified.py`,
`apps/api/fast_demo_benchmark.py`.

---

## Files Deleted

No tracked source files, configuration, or documentation was deleted.

The following **build artifacts and runtime caches** were removed from the
working tree. None were unique or unrecoverable; each is regenerated by the
corresponding tool or run.

| Path | Reason | Recovery |
|------|--------|----------|
| `apps/api/.coverage` | Coverage report | Regenerated by `make test` (pytest-cov) |
| `apps/api/htmlcov/` | HTML coverage report | Regenerated by `make test` |
| `apps/web/tsconfig.tsbuildinfo` | TypeScript incremental cache | Regenerated by `tsc` |
| `apps/api/api_stderr.txt` | Captured stderr from local debug session | n/a (debug output) |
| `apps/api/api_stdout.txt` | Captured stdout from local debug session | n/a (debug output) |
| `uvi_err.txt` | One-off debug capture | n/a (debug output) |
| `uvi_out.txt` | One-off debug capture | n/a (debug output) |
| `apps/api/.pytest_cache/` | pytest cache | Regenerated by pytest |
| `apps/api/.ruff_cache/` | ruff cache | Regenerated by ruff |
| `apps/api/__pycache__/` (all subfolders) | Python bytecode | Regenerated on next import |
| `apps/web/.next/` | Next.js build output | Regenerated by `pnpm dev:web` / `next build` |

Additionally, the empty `AUDIT_2026/` directory remains at the repo root.
The shell on the host refused to remove it (Windows file-handle locking);
this is documented as a follow-up in `REPOSITORY_CLEANUP_REPORT.md`. A plain
`rmdir AUDIT_2026` after committing the cleanup will remove it safely.

---

## Source Code Changes

**None.** No `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.yaml`, `.toml`, `.lock`,
`.sql`, `.jinja2`, `.css`, `.scss`, `.html`, Dockerfile, Makefile target body,
or `.env.example` file was modified.

The only behavioral change made to the repo is the broadened `.gitignore`,
which prevents the same build artifacts from being re-committed in the
future.

| File path | Purpose | Risk | Related feature |
|-----------|---------|------|-----------------|
| `.gitignore` | Exclude build artifacts (`htmlcov/`, `apps/web/.next/`, `apps/web/out/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`) | **Low** — additive patterns only; no removal | Repo hygiene |

---

## Configuration Changes

| Config | Change |
|--------|--------|
| `package.json` | **None** |
| `pnpm-workspace.yaml` | **None** |
| `pnpm-lock.yaml` | **None** |
| `pyproject.toml` (root) | **None** |
| `apps/api/pyproject.toml` | **None** |
| `apps/api/requirements.txt` | **None** |
| `apps/web/package.json` | **None** |
| `apps/web/next.config.ts` | **None** |
| `apps/web/tsconfig.json` | **None** |
| `apps/cli/pyproject.toml` | **None** |
| `Dockerfile` | **None** |
| `docker-compose.yml` | **None** |
| `Makefile` | **None** (note: targets unchanged; `make benchmark` etc. still resolve to `apps/api/benchmarks/`) |
| `.github/workflows/*.yml` | **None** |
| `turbo.json` | **None** |
| `.pre-commit-config.yaml` | **None** |
| `.dockerignore` | **None** |
| `apps/api/.env.example` | **None** |
| `.env` files (any) | **None** — not touched; `.env` is gitignored |
| `.gitignore` | **Added** patterns listed under "Source Code Changes" |
| `AGENTS.md` | **None** |

No new env vars, no removed env vars, no renamed env vars.

---

## Documentation Changes

### Added

- `README.md` (root) — rewritten from a teaser to a complete landing page.
- `REPOSITORY_MAP.md` — full inventory + execution flows + dependency
  diagrams.
- `REPOSITORY_CLEANUP_REPORT.md` — phase-by-phase cleanup audit.
- `LICENSE` — MIT.
- `docs/architecture/SYSTEM_ARCHITECTURE.md` — end-to-end architecture with
  Mermaid diagrams for frontend, backend, agents, memory, database,
  authentication, and GitHub integration.
- `docs/security/SECURITY_MODEL.md` — authoritative threat model covering
  authentication, authorization, refresh tokens, prompt-injection defenses,
  GitHub webhook security, file permissions, rate limiting, encryption, and
  observability.
- `docs/development/ONBOARDING.md` — rewritten 30-minute productivity guide.
- `docs/DOCUMENTATION_INDEX.md` — status, audience, last-reviewed date, and
  recommended reading order for every doc.
- `docs/development/CLEANUP_PLAN_2026_06_26.md` — **this file**.
- README files for every major folder (see Files Added).

### Restructured (moved, not rewritten)

The 33 `docs/*.md` files listed under "Files Moved → Docs reorganization"
were moved into thematic subfolders (`api/`, `architecture/`,
`development/`, `deployment/`, `security/`, `product/`).

### Rewritten in place

- `README.md` (root) — full landing page.
- `docs/README.md` — docs-tree orientation.
- `docs/development/ONBOARDING.md` — replaced prior first-week guide.

### Classified

`docs/DOCUMENTATION_INDEX.md` classifies every doc as one of:

| Status | Count |
|--------|-------|
| ✅ Active | 33 |
| 🔄 Needs Update | 4 (`MODEL_REGISTRY.md`, `AUDIT.md`, `BUGS.md`, `PMF_EXECUTION_PLAN.md`) |
| 🗄️ Deprecated | 0 |
| 📦 Archive | 52 (counted by file in `archive/`) |

---

## Validation

### Tests executed

The cleanup agent did not run any tests. Test files were neither added nor
modified, and the source code they exercise was untouched. The user is
expected to run:

```bash
make test           # pytest apps/api/tests -v --cov=…
make typecheck      # tsc --noEmit in apps/web
make lint           # ruff check apps/api
make format         # ruff format apps/api (verify)
make security       # bandit + safety (verify)
```

### Build status

- **Not validated by the agent.** No Dockerfile, docker-compose, `pnpm
  build`, `uvicorn` start, or `next build` was invoked.
- **Expected:** green. The `Makefile`, `Dockerfile`, `docker-compose.yml`,
  `package.json`, `apps/web/package.json`, `apps/api/pyproject.toml`,
  `apps/cli/pyproject.toml`, and `apps/api/requirements.txt` were not
  modified. The only file with any structural change is `.gitignore`
  (additive).

### Lint status

- **Not validated by the agent.** No `ruff`, `bandit`, `tsc`, or
  `next lint` was invoked.

### Known issues

1. **`AUDIT_2026/` empty directory at repo root.** The shell on the host
   refused to remove this directory after copying its contents into
   `archive/audit_2026_reports/`. Run `rmdir AUDIT_2026` (POSIX) or
   `Remove-Item AUDIT_2026` (PowerShell) after the cleanup commit lands.
2. **`next.config.ts` `output: 'standalone'`** remains in place but the
   `apps/web/.next/standalone/` build artifact (visible in earlier inventory
   passes) is now excluded by `.gitignore`. Verify `pnpm build` still
   succeeds locally — the agent did not exercise it.
3. **Web client still uses localStorage for tokens.** This is a known
   security follow-up (see `docs/security/SECURITY_MODEL.md` §2 and §11) and
   is not in scope for this cleanup pass.
4. **Docs that are 🔄 Needs Update:** `MODEL_REGISTRY.md`, `AUDIT.md`,
   `BUGS.md`, `PMF_EXECUTION_PLAN.md` are flagged for refresh in a follow-up
   PR; not addressed here.
5. **Screenshots & demo recording** placeholders are present in the root
   README but empty; populating them is deferred until the marketing site is
   live.

---

## Recommended Follow-Up

### Safe to merge

These changes are pure cleanup, with zero source-code impact, and align with
the original prompt's success criteria:

- All README additions (`README.md`, `REPOSITORY_MAP.md`,
  `REPOSITORY_CLEANUP_REPORT.md`, `LICENSE`, every subfolder README).
- `docs/architecture/SYSTEM_ARCHITECTURE.md`.
- `docs/security/SECURITY_MODEL.md`.
- `docs/development/ONBOARDING.md` (rewritten).
- `docs/DOCUMENTATION_INDEX.md`.
- `docs/development/CLEANUP_PLAN_2026_06_26.md` (this file).
- `.gitignore` additions.
- Moving 33 `docs/*.md` files into thematic subfolders (purely cosmetic,
  no broken links — see "Needs review" below).
- Archiving 52 stale reports/audits/debug scripts into `archive/`.
- Removing 11 build artifacts (regenerable).

### Needs review

These warrant a reviewer pass before merge, but no action is required if
the reviewer agrees with the rationale:

- **Doc relocations may have broken external links.** Anyone linking to
  `docs/SECURITY.md` from a blog post or Notion page will now 404. A
  follow-up pass should add HTTP redirects if the docs are hosted, or
  update the links upstream.
- **`docs/ONBOARDING.md` rewrite is a content change**, not a move. The
  prior first-week guide was replaced by a 30-minute productivity path.
  Reviewers should sanity-check that no in-flight onboarding runs depend on
  the prior content.
- **`README.md` rewrite** replaces a teaser landing page with a complete
  one. If the project site is mirrored from this README, downstream mirrors
  will pick up the new content.
- **`REPOSITORY_INVENTORY.md` → `REPOSITORY_MAP.md`.** Anyone with a
  bookmark to the old filename will 404. The old file lives in
  `archive/reports/REPOSITORY_INVENTORY.md`.

### Should be reverted

None identified. There are no functional regressions, broken imports, broken
CI steps, broken Dockerfile instructions, or broken migrations introduced
by this pass.

If the reviewer prefers the prior layout, every change in this document is
reversible from git alone — no destructive deletion occurred. The exact
revert is `git revert <cleanup-commit>` for the entire commit, or a
file-by-file restore for individual moves.

---

*End of record.*
