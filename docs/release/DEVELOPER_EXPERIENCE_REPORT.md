# Developer Experience Report

`Version: 1.0` · `Audit Focus: Onboarding, Setup Friction & Tooling Checks`

This report evaluates the developer onboarding journey, from fresh repository clone to running tasks, highlighting setup friction points and command-line execution audits.

---

## 1. Fresh-Clone Installation Timeline

A typical developer setup takes approximately **4–6 minutes** to fully initialize:

1.  **Clone & Docker Boot** (~45s):
    ```bash
    git clone https://github.com/your-org/AgentForge.git
    cd AgentForge
    docker compose up -d
    ```
2.  **API Backend Setup** (~2m):
    ```bash
    cd apps/api
    python -m venv venv
    .\venv\Scripts\Activate.ps1  # Windows PowerShell
    pip install -r requirements.txt
    cp .env.example .env
    ```
3.  **Web Client Initialization** (~1m 30s):
    ```bash
    cd ../web
    pnpm install
    pnpm dev
    ```
4.  **Verification Check** (~30s):
    Accessing the API Swagger docs (`http://localhost:8000/docs`) and opening the login page (`http://localhost:3000/login`).

---

## 2. Onboarding Friction Points

The following friction points have been identified during environment initialization:

### 2.1 Missing Dynamic Python Sandbox Package
The `docker` Python SDK is required for isolated container tests inside the `sandbox_executor.py`, yet it is completely omitted from both `pyproject.toml` and `requirements.txt`. A developer who spins up the API outside of our pre-built development venv will experience sudden runtime errors when triggering tasks that invoke builder/tester nodes.

### 2.2 JWT Verification Library Namespace Conflicts
The presence of `python-jose` in requirements alongside code imports like `import jwt` (which relies on `PyJWT` exceptions) creates potential namespace shadow collisions depending on pip install order. This can lead to cryptic `AttributeError` or `ImportError` exceptions.

### 2.3 Caching & Service Isolation Dependencies
The API fails to start if local PostgreSQL or Redis servers are down. There is no offline sqlite/in-memory database fallback route implemented, making a local docker daemon a hard prerequisite for execution verification loops.

---

## 3. Remediations & Improvements

-   [ ] **Action 1**: Add explicit Node/NPM engine checks to `package.json` to enforce `node >= 22.0.0` and `pnpm >= 9.0.0`.
-   [ ] **Action 2**: Consolidate Python requirements by declaring the `docker` SDK in `pyproject.toml` and removing redundant packages.
