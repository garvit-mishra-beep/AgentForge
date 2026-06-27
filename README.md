<div align="center">

# ⚡ AgentForge

### **The AI-Powered Development Operating System**

*Coordinate a specialized team of AI agents to plan, build, review, and ship software — with your own API keys, on your own infrastructure.*

[![Tests](https://img.shields.io/badge/tests-208%20passing-brightgreen?style=flat-square&logo=pytest)](apps/api/tests/)
[![Type Safety](https://img.shields.io/badge/mypy-0%20errors-blue?style=flat-square)](apps/api/)
[![Linting](https://img.shields.io/badge/ruff-0%20findings-orange?style=flat-square)](apps/api/)
[![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)](apps/api/)

</div>

---

## What is AgentForge?

AgentForge is an open-source multi-agent orchestration platform that replaces the solo developer loop with a coordinated AI engineering team.

You write the task. AgentForge assembles the team, plans the implementation, generates the code, runs the tests, and reviews the output — all streamed live to your dashboard.

**No hosted models. No data sent to third parties. Bring your own API keys.**

---

## ✨ Features

| Feature | Description | Status |
|:---|:---|:---:|
| **Multi-Agent Orchestration** | LangGraph-powered DAG: Lead → Builder → Reviewer → Deliver | ✅ Active |
| **BYOK (Bring Your Own Key)** | Per-user, per-project API key management with AES-256 encryption at rest | ✅ Active |
| **GitHub Native Integration** | Trigger reviews on Pull Requests, auto-post agent findings as PR comments | ✅ Active |
| **Evidence Validation Gate** | Each agent output validated for confidence, completeness, and correctness | ✅ Active |
| **Tree-Sitter Intelligence** | Live symbol index, dependency graphs, and call-scope awareness | ✅ Active |
| **Secure Sandbox Execution** | Generated test suites run in isolated containers | ✅ Active |
| **Vector Memory** | Long-term style and decision recall via pgvector embeddings | ✅ Active |
| **Local Auth (JWT + bcrypt)** | Self-contained user accounts — no third-party auth service required | ✅ Active |
| **Prometheus Metrics** | Structured observability at `/api/v1/metrics` | ✅ Active |
| **Real-time Streaming** | WebSocket-based live agent output delivery | ✅ Active |
| **Enterprise SSO / RBAC** | Multi-tenant team access and role-based controls | 📋 Planned |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (recommended) — or Python 3.10+ and PostgreSQL/Redis installed locally
- An API key from [OpenAI](https://platform.openai.com/), [Anthropic](https://console.anthropic.com/), or [Google AI](https://aistudio.google.com/)

### 1. Clone & Boot

```bash
git clone https://github.com/your-org/AgentForge.git
cd AgentForge

# Spin up PostgreSQL + Redis
docker compose up -d
```

### 2. Configure the Backend

```bash
cd apps/api
python -m venv venv && source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set your JWT_SECRET and at least one provider API key
```

### 3. Start the API

```bash
python -m uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (interactive OpenAPI)
```

### 4. Start the Dashboard

```bash
cd ../web
pnpm install && pnpm dev
# → http://localhost:3000
```

### 5. Run Your First Review (CLI)

```bash
cd ../cli
pip install --editable .
agentforge login
agentforge review path/to/your/file.py
```

> **Migrations run automatically** on first startup. No manual SQL setup required.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Developer                                               │
│    ├── Next.js Dashboard  (REST + WebSocket)             │
│    └── Python CLI         (REST)                         │
│                │                                         │
│         FastAPI Backend (port 8000)                      │
│           ├── Auth (JWT/bcrypt)                          │
│           ├── BYOK Key Manager (AES-256)                 │
│           ├── GitHub App Webhooks                        │
│           └── Agent Orchestrator                         │
│                    │                                     │
│         LangGraph Workflow Engine                        │
│           Team Lead → Builder → Reviewer → Deliver       │
│                    │                                     │
│     ┌──────────────┴──────────────┐                      │
│  PostgreSQL + pgvector       Redis Pub/Sub               │
│  (tasks, users, memory)      (real-time streaming)       │
└─────────────────────────────────────────────────────────┘
```

### The Agent Workflow

```
User Task
   │
   ▼
Team Lead      ← Plans implementation, scopes files, assigns roles
   │
   ▼
Builder        ← Generates code against the plan
   │
   ▼
Reviewer       ← Audits output for correctness, security, style
   │
   ▼
Deliver        ← Synthesizes final output, posts to dashboard or PR
```

Each step is bounded by configurable timeouts, retry limits, and evidence validation checkpoints.

---

## 🔑 BYOK Key Management

AgentForge never stores plaintext API keys. Every credential is:

1. **Validated** — format-checked and live-tested against the provider API before saving
2. **Encrypted** — AES-256 Fernet symmetric encryption at rest
3. **Scoped** — resolved at runtime: user-key → project-key → system-key

```bash
# Add your key via the dashboard, or via API:
POST /api/v1/keys
{
  "provider": "openai",
  "key": "sk-..."
}
```

Supported providers: **OpenAI**, **Anthropic**, **Google Gemini**, **OpenRouter**, **Groq**

---

## 🔗 GitHub Native Integration

Install the AgentForge GitHub App on any repository:

- **PR Review Trigger:** Every Pull Request automatically receives an AI review
- **Inline Comments:** Findings are posted as GitHub PR review comments
- **HMAC Validation:** Webhook payloads verified via `X-Hub-Signature-256`

---

## 🧪 Testing & Quality

```bash
# All 208 tests
python -m pytest

# Type checking
python -m mypy apps/api

# Linting
python -m ruff check apps/api
```

| Check | Result |
|:---|:---|
| Tests | 208 / 208 ✅ |
| Mypy | 0 errors ✅ |
| Ruff | 0 findings ✅ |

---

## 📂 Repository Structure

```
AgentForge/
├── apps/
│   ├── api/              # FastAPI backend, agent graph, database layer
│   │   ├── agents/       # LangGraph nodes (lead, builder, reviewer, etc.)
│   │   ├── app/          # Routes, auth, WebSocket handlers
│   │   ├── core/         # Config, encryption, providers, observability
│   │   ├── migrations/   # SQL migration scripts (auto-applied on boot)
│   │   └── tests/        # 208 pytest tests
│   ├── web/              # Next.js 15 App Router dashboard
│   └── cli/              # Python Click CLI (`agentforge` command)
│
├── docs/                 # Full documentation vault
│   ├── getting-started/  # ONBOARDING.md, SETUP.md
│   ├── architecture/     # SYSTEM_ARCHITECTURE.md, TECH_SPEC.md, SCHEMA.md
│   ├── agents/           # AGENT_SYSTEM.md
│   ├── api/              # API_REFERENCE.md
│   ├── security/         # SECURITY_MODEL.md, DATA_PRIVACY.md
│   └── release/          # Release audit reports and readiness docs
│
├── scripts/              # Developer utilities and validation scripts
├── docker-compose.yml    # PostgreSQL + Redis local stack
├── Dockerfile            # Production API container (multi-stage)
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

---

## 📖 Documentation

| Document | Description |
|:---|:---|
| [Onboarding Guide](docs/getting-started/ONBOARDING.md) | First-time developer setup walkthrough |
| [Environment Setup](docs/getting-started/SETUP.md) | All environment variables and configuration reference |
| [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) | Component layout and data flows |
| [Agent System](docs/agents/AGENT_SYSTEM.md) | LangGraph nodes, roles, memory, and validation |
| [API Reference](docs/api/API_REFERENCE.md) | REST endpoints and WebSocket protocol |
| [GitHub Integration](docs/integrations/GITHUB.md) | GitHub App installation and webhook setup |
| [Security Model](docs/security/SECURITY_MODEL.md) | Auth, encryption, isolation, and threat model |
| [Release Notes](RELEASE_NOTES.md) | V1.0.0 release highlights |

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before opening a PR.

```bash
# Before submitting any PR:
python -m pytest          # must pass 100%
python -m mypy apps/api   # must be clean
python -m ruff check apps/api  # must be clean
```

---

## 🔒 Security

Found a vulnerability? Please review our [Security Policy](SECURITY.md) and report via the process described there. Do not open a public GitHub issue.

---

## 📄 License

AgentForge is open-source software licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built for engineers who want AI to do the heavy lifting — without giving up control.**

</div>