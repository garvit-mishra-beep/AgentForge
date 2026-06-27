# Developer Onboarding Journey — AgentForge

Welcome to the team! This onboarding guide is designed to get you up to speed, set up your development workspace, and run your first agent validation test.

---

## 1. Developer Prerequisites

Ensure you have the following system dependencies installed:
* **Python:** Version 3.10 or 3.12 (standard CPython).
* **Node.js:** Version 18+ (pnpm packet manager is highly recommended).
* **Database:** PostgreSQL (with `pgvector` extension configured).
* **Cache:** Redis Server.

---

## 2. Onboarding Steps

### Step 1: Code Checkout
Clone the codebase and navigate into your project:
```bash
git clone https://github.com/your-org/AgentForge.git
cd AgentForge
```

### Step 2: Initialize Infrastructure
The easiest way to boot local PostgreSQL and Redis is via Docker Compose:
```bash
docker compose up -d
```
This spins up:
* PostgreSQL 16 on port `5432` with the `vector` extension auto-enabled.
* Redis 7 on port `6379`.

### Step 3: Install & Configure backend API
1. Navigate into `apps/api/` and create your python virtual environment:
   ```bash
   cd apps/api
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # On Windows
   # source venv/bin/activate    # On macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment configuration:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your developer local configurations (Database credentials, LLM keys, etc.).

### Step 4: Run the Local Fast Demo Benchmark
We have a benchmark script designed to run the multi-agent graph against standard tasks (like JWT auth generation) locally:
1. Enable fast demo mode defaults:
   ```env
   AGENTFORGE_FAST_DEMO_MODE=true
   ```
2. Start the API locally in one terminal:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. Run the benchmark in a second terminal:
   ```bash
   cd apps/api
   python fast_demo_benchmark.py
   ```
4. Verify all tasks execute without KeyErrors or validation failures.

---

## 3. Local Workspace Checks

To verify your changes before opening a pull request, run the verification scripts:
```bash
# Verify all backend imports compile
python -m compileall apps/api

# Run local pytest validation suite
cd apps/api
python -m pytest
```
Please read our [Contributing Guide](file:///c:/Users/garvi/AgentForge/CONTRIBUTING.md) for pull request policies.
