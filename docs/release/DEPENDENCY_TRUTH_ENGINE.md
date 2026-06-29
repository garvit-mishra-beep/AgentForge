# Dependency Truth Engine

`Version: 1.0` · `Audit Focus: Dependency Categorization, Version Drift & Security Risk Analysis`

This document classifies all third-party dependencies defined in backend and frontend manifests, highlighting version drifts, shadowing package conflicts, and redundant libraries.

---

## 1. Backend Python Dependency Classifications

| Package | Version | Code Usage | Classification | Risk Analysis / Findings |
| :--- | :--- | :--- | :--- | :--- |
| **fastapi** | `0.104.1` | Used in `main.py` and route handlers. | **REQUIRED** | None. Stable version. |
| **uvicorn** | `0.27.0` | Server runner entry point. | **REQUIRED** | None. |
| **python-multipart**| `0.0.6` | Decodes form-data uploads. | **REQUIRED** | None. |
| **python-jose** | `3.3.0` | Token management payload library. | **UNUSED / SHADOWED**| The codebase imports PyJWT namespaces (`import jwt` and PyJWT-specific exceptions `jwt.InvalidTokenError`), yet `PyJWT` is NOT listed in the dependency manifests, while `python-jose` (which provides a conflicting `jwt` top-level namespace) is declared. |
| **asyncpg** | `0.29.0` | Client pool execution connector. | **REQUIRED** | None. |
| **redis** | `5.0.1` | Used for rate limiting. | **REQUIRED** | None. |
| **pydantic** | `2.5.0` | Request validation schemas. | **REQUIRED** | None. |
| **langgraph** | `0.0.22` | Core multi-agent state graph. | **REQUIRED** | None. |
| **langchain** | `0.1.5` | Orchestration dependency. | **UNUSED** | `main.py` explicitly blocks langchain via `sys.modules["langchain"] = None` for startup optimization. It is not imported or used. |
| **openai** | `1.3.0` | API call provider integration. | **REQUIRED** | None. |
| **anthropic** | `0.7.8` | API call provider integration. | **REQUIRED** | None. |
| **google-generativeai**| `0.3.2` | API call provider integration. | **REQUIRED** | None. |
| **cryptography** | `41.0.3` | Encrypts credentials at rest. | **REQUIRED** | None. |
| **bcrypt** | `4.0.1` | Hashes user passwords. | **REQUIRED** | None. |
| **docker** | *N/A* | Spawns sandboxed runtimes. | **MISSING / OPTIONAL**| Dynamically imported inside `sandbox_executor.py` but completely omitted from `pyproject.toml` and `requirements.txt`. Runs successfully only because it is pre-installed in the development virtual environment. |

---

## 2. Frontend Node.js Dependency Classifications

All frontend packages listed in `apps/web/package.json` are verified as active.

-   `next`, `react`, `react-dom` — **REQUIRED** (Core app-router framework)
-   `lucide-react`, `framer-motion` — **REQUIRED** (Theme aesthetics and streaming UI transition controls)
-   `class-variance-authority`, `clsx`, `tailwind-merge` — **REQUIRED** (Style generation utility libraries)
-   `jwt-decode` — **REQUIRED** (Extracts user metadata context from local storage auth tokens)
-   `@radix-ui/react-*` — **REQUIRED** (Primitive UI controls wrapping dialogues, separators, scroll areas, and tools)

---

## 3. High-Priority Remediations

1.  **Resolve JWT Library Shadowing**:
    -   Replace `python-jose` with `PyJWT` in `apps/api/pyproject.toml` and `requirements.txt` to align configuration manifests with actual code import structures (`import jwt` raising PyJWT exceptions).
2.  **Declare Docker SDK explicitly**:
    -   Add `docker` package to the backend requirements files to ensure deployments do not fail due to a missing package when initializing standard container-isolated executes.
3.  **Purge Langchain**:
    -   Remove `langchain` from `pyproject.toml` and `requirements.txt` to drop 15MB+ of unused third-party weight.
