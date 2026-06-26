# AgentForge

**AI-powered multi-agent orchestration platform — replace the single-AI coding assistant with a fully collaborative AI engineering team.**

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-0.3.0--alpha-orange)

---

## Features

- **Multi-Agent Teams** — Assign specialized AI agents (Team Lead, Backend Engineer, Frontend Engineer, QA, Security, DevOps) to every task
- **Structured Workflows** — LangGraph-driven directed graphs with explicit handoffs and conditional branching
- **Real-Time Streaming** — WebSocket-powered live agent output in the browser as each step executes
- **Human-in-the-Loop** — Review, approve, or request changes at every handoff gate
- **Model Flexibility** — Mix GPT-4o, Claude Sonnet, Gemini 1.5 Pro, Qwen-72B per role
- **Team Memory** — pgvector semantic search across past task outputs for long-term context
- **Secure** — Clerk authentication, encrypted API keys, RBAC, audit trails

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/agentforge/agentforge.git
cd agentforge

# Install dependencies (all workspaces)
pnpm install

# Copy environment files
cp .env.example .env
cp apps/api/.env.example apps/api/.env

# Start infrastructure (PostgreSQL + Redis)
docker compose up -d

# Run database migrations
pnpm db:migrate

# Seed with sample data
pnpm db:seed

# Start development servers (Next.js + FastAPI concurrently)
pnpm dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- WebSocket: `ws://localhost:8000/ws/tasks/{task_id}`

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 15 (App Router) | Server components + client streaming + BFF API routes |
| Backend | FastAPI (Python) | Async-first, Pydantic validation, LangGraph integration |
| Agent Orchestration | LangGraph | Directed graph with state persistence, human-in-the-loop interrupts |
| Database | PostgreSQL + pgvector | Structured data + semantic vector search |
| Cache & Messaging | Redis | Pub/sub agent streaming + JWT session cache |
| Auth | Clerk | Hosted UI, OAuth, organization management |
| Monorepo | Turborepo | Incremental builds, parallel tasks, remote caching |
| Deploy | Vercel (FE) + Railway (BE) | Zero-config edge + managed Postgres/Redis |

---

## Folder Structure

```
agentforge/
├── apps/
│   ├── web/                    # Next.js 15 frontend
│   │   ├── app/                # App Router pages
│   │   ├── components/         # Shared React components
│   │   └── lib/                # Client utilities, API client
│   └── api/                    # FastAPI backend
│       ├── app/                # Route handlers, WebSocket handlers
│       ├── agents/             # LangGraph graph definitions, nodes
│       ├── core/               # Auth middleware, config, DB session
│       └── models/             # Pydantic schemas
├── packages/
│   ├── db/                     # Prisma schema + generated client
│   ├── types/                  # Shared TypeScript types
│   └── ui/                     # Shared React component library
├── docker-compose.yml          # PostgreSQL + Redis
├── turbo.json                  # Turborepo configuration
└── package.json                # Root workspace config
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product requirements and vision |
| [TECH_SPEC.md](TECH_SPEC.md) | System architecture and data flow |
| [SCHEMA.md](SCHEMA.md) | Database schema and ER diagram |
| [SETUP.md](SETUP.md) | Development environment setup |
| [API.md](API.md) | Complete REST API and WebSocket reference |
| [CLAUDE.md](CLAUDE.md) | Claude Code session conventions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [DEPLOYMENT.md](DEPLOYMENT.md) | CI/CD and deployment |

---

## License

MIT — see [LICENSE](../LICENSE)
