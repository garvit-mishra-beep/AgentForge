# `scripts/` — Operational Scripts

Standalone scripts that operate across apps or perform one-off maintenance.
Each script is self-documenting via `--help`.

## What Belongs Here

- Database seeding, snapshotting, or migration helpers that don't belong inside
  the API runtime.
- Local-dev convenience scripts (e.g. reset-and-reseed, demo-data generator).
- One-off operational scripts (e.g. token rotation, key rotation).
- Cross-cutting tooling used by both `apps/api` and `apps/web`.

## What Does NOT Belong Here

- Application code — that belongs in `apps/api/app/`, `apps/api/agents/`, etc.
- Ad-hoc debug helpers — archive them in `archive/debug_scripts/` instead.
- CI logic — that belongs in `.github/workflows/`.

## Conventions

- Top-level shebang: `#!/usr/bin/env python3` (or `bash`) as appropriate.
- Use `argparse` and provide `--help`.
- Never hardcode secrets — load from environment.
- Never reach into app internals without going through their public APIs.

## Related Modules

- Root `Makefile` exposes user-friendly aliases over scripts in this folder.