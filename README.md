# AgentForge

### **The Multi-Agent AI Workforce Orchestrator**

AgentForge is a self-hosted platform designed to coordinate teams of specialized AI agents (Lead, Builder, Reviewer, Tester) to plan, build, review, and test code. Bring your own keys, keep your source code on your own infrastructure, and monitor agent collaborations in real-time.

---

## Why AgentForge Exists

Most AI tools operate as simple chat interfaces or solo agent loops. Real engineering, however, relies on collaboration and validation gates. AgentForge wraps specialized agent roles in a structured **LangGraph State Graph**, fanning out tasks to builders, running code in isolated **Docker sandboxes**, and routing outputs through automated review and test validators before sign-off.

---

## System Architecture

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                        Next.js Client                       │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ HTTPS REST / WebSockets
  ┌──────────────────────────────▼──────────────────────────────┐
  │                     FastAPI Gateway Server                  │
  └──────┬───────────────────────┬───────────────────────┬──────┘
         │                       │                       │
  ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
  │  PostgreSQL │         │    Redis    │         │  LangGraph  │
  │  (Storage)  │         │(Rate limits)│         │(Engine loop)│
  └─────────────┘         └─────────────┘         └──────┬──────┘
                                                         │
                                                  ┌──────▼──────┐
                                                  │ Docker Host │
                                                  │ (Sandboxes) │
                                                  └─────────────┘
```

- **Frontend**: Next.js App Router client communicating via REST APIs and WebSocket event channels.
- **Backend**: FastAPI server with modular router architecture, PostgreSQL connection pools (`asyncpg`), and Redis rate-limiting.
- **Agent Orchestrator**: LangGraph state machine tracking agent state transitions, prompting, and validation outputs.
- **Docker Sandboxes**: Secure, isolated test executors running generated code inside sandboxed containers with strict syscall resource caps.

---

## Capabilities

- **State Graph Pipeline**: Coordinated flow routing tasks between Lead (planning), Builder (code generation), Reviewer (audit), and Tester (verification).
- **Docker Container Sandboxing**: Runs pytest and jest test suites inside secure sandboxed Docker environments with fallback to local process isolation.
- **Local Authentication**: Complete JWT token authentication, password hashing (`bcrypt`), tenant isolation, and sliding window rotating refresh tokens.
- **BYOK (Bring Your Own Key)**: Layered API key resolution (Project → User → Global Settings) encrypted at rest using AES-256 Fernet.
- **Observability**: Live task execution pipelines, metrics tracking, and stdout log collectors.

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.11+**
- **Node.js 22+** and **pnpm**

### 1. Boot Local Services
Spin up PostgreSQL and Redis:
```bash
docker compose up -d
```

### 2. Configure Backend
Create the API environment settings:
```bash
cd apps/api
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
# Edit .env — set your JWT_SECRET and add your LLM provider API keys
```

### 3. Run Migrations & Start Backend
The backend auto-runs database schema migrations on launch:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Start Web Dashboard
```bash
cd ../web
pnpm install
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) to access the dashboard.

---

## API Overview

All core REST endpoints are versioned under `/api/v1`:

- `POST /auth/register` — Create a new developer account.
- `POST /auth/login` — Authenticate and retrieve JWT token pair.
- `POST /tasks` — Submit a task to the orchestrator queue.
- `GET /tasks/{task_id}/messages` — Fetch task execution logs.
- `GET /teams` — Retrieve available agent teams.
- `PUT /teams/{team_id}` — Edit team models configurations.

---

## Security

1. **Sandboxing**: Generated files are executed in non-root Docker sandboxes with dropped Linux capabilities and custom seccomp profiles to prevent breakout.
2. **Key Protection**: Stored API keys are encrypted at rest using Fernet keys configured via environment variables.
3. **Tenant Isolation**: Every API endpoint filters records by the authenticated user's ID to prevent IDOR access.

---

## Testing

Run the backend Pytest suite:
```bash
cd apps/api
.\venv\Scripts\pytest.exe
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.