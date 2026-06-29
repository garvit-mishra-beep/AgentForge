# Dead Code Archaeology

`Version: 1.0` · `Audit Focus: Orphan Packages, Unused Modules & Duplicate Artifacts`

This document details all modules, directories, and files in the repository that are unreachable, unused, or duplicate implementations of active features.

---

## 1. Dead Code Catalog

| Item Pathway | Why It Exists | Last Reference / Context | Removal Risk | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `app/repository_intelligence/` | Designed as a static repository analysis engine for semantic context parsing. | Stood up as an experimental tool; only referenced by `scripts/test_repository_intelligence.py`. | **LOW** — Completely isolated from the main FastAPI server and web client. | **ARCHIVE** (Move to `archive/experimental/`) |
| `app/validation/` | Designed as an automated acceptance testing framework. | Only self-referenced inside its package structure; never imported by external code. | **LOW** — Completely isolated. | **ARCHIVE** (Move to `archive/experimental/`) |
| `apps/agents/` | Stale/duplicate copy of the LangGraph workforce state graph. | Root-level module which was replaced by the runtime module at `apps/api/agents/`. | **LOW** — Backend unit tests and graph calls resolve to the sub-package path under `apps/api/`. | **DELETE** |
| `scripts/test_repository_intelligence.py` | Verification harness for the repository intelligence analyzer. | Unreferenced helper script. | **LOW** | **ARCHIVE** |
| `scripts/test_evidence_gate.py` | Verification harness for the evidence gate logic. | Unreferenced helper script. | **LOW** | **ARCHIVE** |

---

## 2. Recommendation Sign-off

*   **Delete**: Stale duplicate directories (`apps/agents/`).
*   **Archive**: Relocate experimental static analysis frameworks (`app/repository_intelligence/`, `app/validation/`) to `archive/experimental/` to reduce workspace clutter while preserving code history.
