# Archive

This directory contains historical artifacts that have been preserved for context
but are **no longer maintained** and should not be relied upon for current
behavior.

## Why these files were archived

The repository accumulated large numbers of point-in-time reports, marketing
PRDs, audit outputs, and ad-hoc debug scripts during the v1 build-out. Rather
than delete them outright (which would lose institutional memory) they were
moved here. None of the contents in `archive/` are referenced by CI, the
runtime, or the docs index.

## Structure

| Path | Contents | Rationale |
|------|----------|-----------|
| `reports/` | Strategic reviews, PMF plans, readiness reports, demo PRDs | Point-in-time product/strategy writing — superseded by `docs/` |
| `audit_2026_reports/` | Output of the 2026 audit pass (executive summary, security audit, etc.) | Historical audit snapshots |
| `debug_scripts/` | One-off Python helpers (`simple_check.py`, `validation_simple.py`, etc.) and legacy benchmark variants | Ad-hoc scripts from local debugging that have no place in the main API |

## When to add to this folder

Add a file here when **all** of the following are true:

- It is no longer linked from any documentation, README, or code path.
- Removing it outright would lose useful historical context.
- It is not a live source of truth (e.g. not part of the build, test suite,
  or migration chain).

## When NOT to use this folder

- For stale code that is still imported — fix the imports, then archive.
- For temporary scratch files — delete them.
- For generated artifacts — add the pattern to `.gitignore` instead.