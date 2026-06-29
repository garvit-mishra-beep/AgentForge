# Repository Restructuring Plan

`Version: 1.0` · `Audit Focus: Clean Workspace Architecture`

This document details the planned folder structures, file relocations, and deletions designed to clean up the AgentForge repository before the V1 public release.

---

## 1. Directory Actions

### 1.1 Deletions (Unused/Stale)

| Source Path | Target Action | Impact Verification |
| :--- | :--- | :--- |
| `apps/agents/` | **DELETE** | Stale graph layout copy. Active orchestrator lives at `apps/api/agents/`. Checked imports and verified no references resolve here. |

### 1.2 Archivals (Experimental Frameworks)

Move loose, experimental root directories to `archive/experimental/` to isolate them from active runtime directories:

-   `app/repository_intelligence/` ──► `archive/experimental/repository_intelligence/`
-   `app/validation/` ──────────────► `archive/experimental/validation/`
-   `scripts/test_repository_intelligence.py` ──► `archive/experimental/scripts/test_repository_intelligence.py`
-   `scripts/test_evidence_gate.py` ─────────► `archive/experimental/scripts/test_evidence_gate.py`

### 1.3 Root Cleanups

To keep the repository root minimal and focused, move loose reports to `archive/reports/`:

-   `PRE_AUDIT_STATUS.md` ──► `archive/reports/PRE_AUDIT_STATUS.md`

---

## 2. Retained Root Files

After execution, only the following core configuration and standard community files are permitted to remain in the root directory:

```text
/
├── .git/
├── .github/
├── apps/
│   ├── api/
│   ├── cli/
│   └── web/
├── archive/
│   ├── experimental/
│   └── reports/
├── docs/
│   ├── architecture/
│   └── release/
├── .env.example
├── .gitignore
├── .prettierrc
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── Makefile
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── pyproject.toml
├── README.md
├── SECURITY.md
└── turbo.json
```
