# DEPENDENCY_RECONCILIATION_REPORT.md

## AgentForge Dependency Reconciliation Report

**Date**: 2026-06-28  
**Status**: PARTIAL (Actual installed environment inaccessible)  
**Note**: The executed environment blocked package enumeration commands (pip freeze, pip list), preventing collection of actual installed package data. Therefore, the "ACTUAL_DEPENDENCIES.txt" file could not be generated, and classification of packages as Required/Optional/Dev-only/Transitive cannot be performed with verified evidence.

## Files Compared

1. **INFERRED_DEPENDENCIES.txt** (renamed from original ACTUAL_DEPENDENCIES.txt)  
   - Path: `C:\Users\garvi\AgentForge\INFERRED_DEPENDENCIES.txt`  
   - Content: Exact versions derived from source code analysis (see below)

2. **requirements.txt**  
   - Path: `C:\Users\garvi\AgentForge\apps\api\requirements.txt`  
   - Content: Exact versions derived from source code analysis

3. **pyproject.toml**  
   - Path: `C:\Users\garvi\AgentForge\apps\api\pyproject.tomliteral.toml`  
   - Content: Version ranges for dependencies (missing one package)

4. **ACTUAL_DEPENDENCIES.txt** (expected)  
   - Status: **NOT GENERATED** – required command `pip freeze > ACTUAL_DEPENDENCIES.txt` could not be executed due to environment restrictions.

## File Contents

### INFERRED_DEPENDENCIES.txt / requirements.txt (identical)
```
# AgentForge API Dependencies
# Extracted from imports in source code
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
asyncpg==0.29.0
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
langchain==0.1.5
langgraph==0.0.22
openai==1.3.0
anthropic==0.7.8
google-generativeai==0.3.2
httpx==0.25.0
cryptography==41.0.3
bcrypt==4.0.1
jinja2==3.1.2
```

### pyproject.toml (dependencies section)
```toml
dependencies = [
    "fastapi>=0.104.0,<0.105.0",
    "uvicorn[standard]>=0.27.0,<0.28.0",
    "python-multipart>=0.0.6,<0.0.7",
    "python-jose[cryptography]>=3.3.0,<4.0.0",
    "passlib[bcrypt]>=1.7.4,<1.8.0",
    "python-dotenv>=1.0.0,<2.0.0",
    "asyncpg>=0.29.0,<0.30.0",
    "redis>=5.0.0,<6.0.0",
    "pydantic>=2.5.0,<3.0.0",
    "langchain>=0.1.0,<0.2.0",
    "langgraph>=0.0.20,<0.1.0",
    "openai>=1.3.0,<2.0.0",
    "anthropic>=0.7.0,<0.8.0",
    "google-generativeai>=0.3.0,<0.4.0",
    "httpx>=0.25.0,<0.26.0",
    "cryptography>=41.0.0,<42.0.0",
    "bcrypt>=4.0.1,<5.0.0",
    "jinja2>=3.1.0,<4.0.0",
]
```

## Comparison Summary

| Package | INFERRED/requirements.txt | pyproject.toml | Notes |
|---------|---------------------------|----------------|-------|
| fastapi | ==0.104.1 | >=0.104.0,<0.105.0 | Compatible version range |
| uvicorn[standard] | ==0.24.0 | >=0.27.0,<0.28.0 | **Incompatible**: 0.24.0 < 0.27.0 minimum |
| python-multipart | ==0.0.6 | >=0.0.6,<0.0.7 | Compatible |
| python-jose[cryptography] | ==3.3.0 | >=3.3.0,<4.0.0 | Compatible |
| passlib[bcrypt] | ==1.7.4 | >=1.7.4,<1.8.0 | Compatible |
| python-dotenv | ==1.0.0 | >=1.0.0,<2.0.0 | Compatible |
| asyncpg | ==0.29.0 | >=0.29.0,<0.30.0 | Compatible |
| redis | ==5.0.1 | >=5.0.0,<6.0.0 | Compatible |
| pydantic | ==2.5.0 | >=2.5.0,<3.0.0 | Compatible |
| **pydantic-settings** | ==2.1.0 | **MISSING** | **Critical omission** |
| langchain | ==0.1.5 | >=0.1.0,<0.2.0 | Compatible |
| langgraph | ==0.0.22 | >=0.0.20,<0.1.0 | Compatible |
| openai | ==1.3.0 | >=1.3.0,<2.0.0 | Compatible |
| anthropic | ==0.7.8 | >=0.7.0,<0.8.0 | Compatible |
| google-generativeai | ==0.3.2 | >=0.3.0,<0.4.0 | Compatible |
| httpx | ==0.25.0 | >=0.25.0,<0.26.0 | Compatible |
| cryptography | ==41.0.3 | >=41.0.0,<42.0.0 | Compatible |
| bcrypt | ==4.0.1 | >=4.0.1,<5.0.0 | Compatible |
| jinja2 | ==3.1.2 | >=3.1.0,<4.0.0 | Compatible |

## Key Findings

1. **uvicorn version mismatch**:  
   - `requirements.txt` specifies `uvicorn[standard]==0.24.0`  
   - `pyproject.toml` requires `>=0.27.0,<0.28.0`  
   - The version in requirements.txt (0.24.0) does not satisfy the minimum version (0.27.0) in pyproject.toml.  
   - This would cause `pip install .` to attempt to upgrade uvicorn to at least 0.27.0, potentially leading to a différent version than specified in requirements.txt.

2. **Missing pydantic-settings in pyproject.toml**:  
   - The package `pydantic-settings==2.1.0` is present in both INFERRED_DEPENDENCIES.txt and requirements.txt but **absent** from pyproject.toml.  
   - This omission would cause `pip install .` to fail with `ModuleNotFoundError: No module named 'pydantic_settings'` when the application imports `pydantic_settings`.

3. **No actual installed package data available**:  
   - The environment blocked execution of `pip freeze` and `pip list`, preventing generation of the `ACTUAL_DEPENDENCIES.txt` file.  
   - Without the actual installed packages, it is impossible to classify each package as Required, Optional, Dev-only, or Transitive based on verified evidence.

## Classification Attempt (Based on Inference Only – Not Verified)

*Note: The following classification is derived from import analysis and is **not** verified against an actual installed environment. It is presented for reference only.*

| Package | Likely Classification | Reasoning |
|---------|----------------------|-----------|
| fastapi | Required | Directly imported in main.py |
| uvicorn[standard] | Required | Used to run the application |
| python-multipart | Required | For handling file uploads |
| python-jose[cryptography] | Required | For JWT handling |
| passlib[bcrypt] | Required | For password hashing |
| python-dotenv | Required | For loading environment variables |
| asyncpg | Required | PostgreSQL async driver |
| redis | Required | Redis caching client |
| pydantic | Required | Data validation and settings |
| pydantic-settings | Required | For settings management |
| langchain | Required | Agent orchestration framework |
| langgraph | Required | State graph for agents |
| openai | Optional | OpenAI API integration (only if used) |
| anthropic | Optional | Anthropic API integration (only if used) |
| google-generativeai | Optional | Google AI integration (only if used) |
| httpx | Required | HTTP client for external API calls |
| cryptography | Required | Underlying cryptographic library |
| bcrypt | Transitive | Comes via passlib[bcrypt] |
| jinja2 | Required | For templating (if used) or transitive |

## Required Action for Authoritative Resolution

To produce a definitive `DEPENDENCY_RECONCILIATION_REPORT.md` and an authoritative `requirements.txt`, the following must be performed in an environment where the application runs successfully (208 passing tests, 0 mypy errors, 0 ruff findings):

1. Activate the verified virtual environment.
2. Execute: `pip freeze > ACTUAL_DEPENDENCIES.txt`
3. Compare `ACTUAL_DEPENDENCIES.txt` against `INFERRED_DEPENDENCIES.txt`, `requirements.txt`, and `pyproject.toml`.
4. Classify each package by examining its usage in the codebase (import analysis) and checking if it is a direct dependency or transitive.
5. Generate an authoritative `requirements.txt` that exactly matches `ACTUAL_DEPENDENCIES.txt` (or the verified subset of direct dependencies).
6. Update `pyproject.toml` to include all dependencies from the authoritative list with appropriate version constraints (preferably matching the exact versions from the verified environment for reproducibility).
7. Ensure `requirements.txt` and `pyproject.toml` are consistent.

## Current Blockers

- **Environment Restriction**: Cannot execute `pip freeze` or similar commands to obtain ground-truth installed packages.
- **Dependency Inconsistency**: The `pyproject.toml` file is missing `pydantic-settings` and has an incompatible version range for `uvicorn[standard]`.

## Immediate Required Fix (Based on Available Evidence)

To allow `pip install .` to succeed, the following changes are **required** in `apps/api/pyproject.toml`:

1. Add `"pydantic-settings>=2.1.0,<3.0.0",` to the dependencies list.
2. Adjust the `uvicorn[standard]` version range to include 0.24.0 (e.g., `>=0.24.0,<0.25.0`) or align the versions across files.

*Note: This fix is based on the analysis of the available files and would need validation in the actual environment once accessible.*

---

**Conclusion**: Without access to the actual installed package set, this report remains provisional. The critical omission of `pydantic-settings` from `pyproject.toml` and the version mismatch for `uvicorn[standard]` are clear discrepancies that must be resolved to achieve consistent installation across `pip install .` and `pip install -r requirements.txt`.