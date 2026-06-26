# Architecture Decision Records — AgentForge

---

## ADR-001: LangGraph over AutoGen / CrewAI

**Status:** Accepted | **Date:** 2026-05-10

### Context
AgentForge needed an agent orchestration framework. The options were LangGraph (LangChain), AutoGen (Microsoft), and CrewAI. Requirements: explicit control flow (not black-box), state persistence, conditional branching, human-in-the-loop interrupts, debugging/replay support.

### Decision
Use **LangGraph** as the agent orchestration layer.

### Rationale
- **Directed graph model** — LangGraph models workflows as explicit DAGs, not black-box agent loops. Every node (agent step) and edge (handoff) is defined in code.
- **State persistence** — LangGraph maintains a TypedDict state across nodes. The full task state survives interruptions, errors, and restarts.
- **Conditional branching** — Edges can route based on state values (e.g., "if review found blocking issues → route back to backend"). This maps directly to the review gate pattern.
- **Human-in-the-loop interrupts** — LangGraph has built-in interrupt/resume at any node. No custom implementation needed.
- **Replay and debugging** — LangGraph supports replay of any historical run from state, enabling debugging of agent behavior.

### Consequences
- Team must learn LangGraph concepts (StateGraph, nodes, edges, conditional routing)
- Locked into LangChain ecosystem (but can abstract AI provider calls behind an interface)
- LangGraph is younger than AutoGen; API changes are expected

### Alternatives Rejected
- **AutoGen** — AssistantAgent pattern is powerful but control flow is implicit and harder to audit. Less suited for structured review gates.
- **CrewAI** — Higher-level abstraction but less control over step-by-step execution. No built-in human-in-the-loop. Harder to debug.

---

## ADR-002: FastAPI over Express (Node.js)

**Status:** Accepted | **Date:** 2026-05-08

### Context
The backend needed to support: async REST API, WebSocket connections, integration with Python-first AI SDKs (LangChain/LangGraph, OpenAI, Anthropic, Google Generative AI).

### Decision
Use **FastAPI (Python)** for the backend API.

### Rationale
- **Python AI ecosystem** — LangGraph, LangChain, OpenAI SDK, Anthropic SDK, Google Generative AI SDK are all Python-first or Python-only. Using a Node.js backend would require wrapping these in a sidecar service.
- **Async native** — FastAPI is built on asyncio. WebSocket handling, async DB queries, and concurrent AI provider calls all benefit from this.
- **Pydantic validation** — Automatic request/response schema validation with type hints. Generates OpenAPI docs automatically.
- **Performance** — FastAPI benchmarks near the top of Python web frameworks (on par with Node.js for typical API workloads).

### Consequences
- Backend and frontend are in different languages — requires developers to be proficient in both Python and TypeScript
- Deployment requires a Python runtime (handled via Docker on Railway)

### Alternatives Rejected
- **Express (Node.js)** — Would require running Python sidecar for agent execution, adding network latency and operational complexity.
- **Go** — Excellent performance but lacks mature AI SDK ecosystem. Would need to build all AI provider clients from scratch.

---

## ADR-003: Clerk over Auth.js / Supabase Auth

**Status:** Accepted | **Date:** 2026-05-12

### Context
AgentForge needed authentication with: email/password, Google OAuth, GitHub OAuth, session management, JWT validation, organization support (Team plan multi-seat).

### Decision
Use **Clerk** for authentication.

### Rationale
- **Hosted UI** — Clerk provides pre-built sign-in/sign-up pages. No need to build auth UI from scratch.
- **Organization management** — Built-in support for teams/orgs with role-based access. Needed for Team plan multi-seat feature.
- **Webhook events** — User lifecycle events (created, updated, deleted) via webhooks. Enables syncing Clerk users to the AgentForge database.
- **JWT validation middleware** — Clerk provides a FastAPI JWT validation library. Middleware implementation was straightforward.

### Consequences
- Vendor lock-in on Clerk's pricing model
- Must handle Clerk webhooks for user data synchronization
- User data lives in Clerk's system, duplicated in AgentForge DB for performance

### Alternatives Rejected
- **Auth.js (NextAuth)** — Great for Next.js but no FastAPI backend support. Would need separate auth for the API layer. No organization management.
- **Supabase Auth** — Good auth but tied to Supabase ecosystem. AgentForge already uses Railway for Postgres, so adding Supabase would be a second vendor.

---

## ADR-004: PostgreSQL + pgvector over MongoDB

**Status:** Accepted | **Date:** 2026-05-09

### Context
The database needed to store: relational structured data (users, projects, teams, tasks, steps), and vector embeddings for agent memory (semantic search over past task outputs).

### Decision
Use **PostgreSQL 16 with pgvector extension**.

### Rationale
- **Single database** — Both relational data and vector embeddings in one database. No ETL pipeline between Postgres and a vector DB.
- **Strong relational model** — The data model (projects → teams → agents → tasks → steps → messages/outputs) is deeply relational. Joins, foreign keys, and constraints are natural.
- **pgvector maturity** — pgvector is production-stable, supports IVFFLAT and HNSW indexes, and provides cosine similarity search with good performance (sub-100ms for top-5 retrieval at 10k vectors).
- **Transactionality** — ACID guarantees for task state transitions. Critical for correctness in agent execution.

### Consequences
- pgvector is less performant than dedicated vector DBs at very large scale (>1M vectors). Switch to Pinecone or Qdrant if AgentForge grows beyond that threshold.
- Requires PostgreSQL 16 (incompatible with older versions)

### Alternatives Rejected
- **MongoDB** — No native vector search (at time of decision). Schema flexibility is not needed — the data model is well-defined. Losing foreign key constraints made it unsuitable.
- **PostgreSQL + Pinecone** — Would require maintaining two database systems and synchronizing data between them. Operational complexity not justified at current scale.

---

## ADR-005: Redis Pub/Sub for Agent Messaging

**Status:** Accepted | **Date:** 2026-05-15

### Context
Agent execution generates real-time events (agent started, token stream, agent complete, handoff, task complete) that need to reach the browser. Evaluation: polling, WebSocket direct, Redis pub/sub + WebSocket relay.

### Decision
Use **Redis pub/sub** as the message broker, with FastAPI WebSocket server subscribing to Redis channels and relaying to browser connections.

### Rationale
- **Decoupling** — Agent nodes publish events to Redis channels. The WebSocket server subscribes independently. No direct coupling between agent execution and WebSocket connections.
- **Multiple subscribers** — Multiple WebSocket server instances can subscribe to the same Redis channel for horizontal scaling.
- **Persistence not needed** — Agent events are ephemeral; they don't need to survive Redis restarts. If a WebSocket disconnects, missed events can be recovered from the database (task_steps table).
- **Sub-millisecond latency** — Redis pub/sub is fast enough for streaming token chunks.

### Consequences
- Redis becomes a dependency for real-time functionality
- If Redis goes down, agent execution continues but WebSocket updates stop (task results still saved to DB)

### Alternatives Rejected
- **Direct WebSocket between agent and browser** — Agents run as Python coroutines, not as separate processes. No clean way to manage per-task WebSocket connections from within a LangGraph node.
- **Server-Sent Events (SSE)** — Unidirectional. Agent execution needs to receive human approval signals, which is bidirectional.

---

## ADR-006: WebSockets over Server-Sent Events

**Status:** Accepted | **Date:** 2026-05-15

### Context
The frontend needed real-time updates for agent execution (streaming token output, step completion, approval requests) and the ability to send signals back (human approval/rejection).

### Decision
Use **WebSockets** for real-time communication.

### Rationale
- **Bidirectional** — Human approval requires sending data from browser → server. SSE is unidirectional (server → client).
- **Low latency** — WebSocket provides full-duplex communication with minimal overhead after connection establishment.
- **Standard protocol** — Native browser WebSocket API, no client library needed.
- **Connection lifecycle** — Explicit open/close gives clear connection state. Auto-reconnect logic is straightforward.

### Consequences
- WebSocket connections require sticky sessions or a shared state store (Redis pub/sub) for multi-instance deployments
- Connection limits: browser caps at ~6 concurrent WebSocket connections per origin

### Alternatives Rejected
- **SSE** — Unidirectional, not suitable for human approval signals. Requires polyfill for browser support.
- **Polling** — Too slow for token-level streaming. Unacceptable user experience for real-time agent output.

---

## ADR-007: Turborepo for Monorepo Management

**Status:** Accepted | **Date:** 2026-05-07

### Context
AgentForge has multiple deployable apps (Next.js frontend, FastAPI backend) and shared packages (db, types, ui). Needs build orchestration, caching, and parallel execution.

### Decision
Use **Turborepo** for monorepo management.

### Rationale
- **Incremental builds** — Turborepo caches task outputs. Only rebuild what changed. Dev startup time is seconds (not minutes).
- **Parallel execution** — `pnpm dev` starts both Next.js and FastAPI concurrently. CI runs lint + test for all workspaces in parallel.
- **Remote caching** — Share build cache across CI runners and developer machines via Vercel Remote Caching.
- **Simple configuration** — `turbo.json` with pipeline definitions is straightforward. No complex Nx project graph configuration needed.

### Consequences
- Must maintain `turbo.json` pipeline definitions as the project grows
- Remote caching requires Vercel account (free tier available)

### Alternatives Rejected
- **Nx** — More powerful but more complex. Nx's project graph, code generation, and plugin system are overkill for this project size.
- **pnpm workspaces only** — No task orchestration or caching. Each developer would need to run build commands individually.

---

## ADR-008: Railway over AWS / Heroku

**Status:** Accepted | **Date:** 2026-05-20

### Context
AgentForge needed deployment infrastructure for: FastAPI Python backend, PostgreSQL database, Redis cache. Options: Railway, AWS (ECS/EKS), Heroku, Fly.io.

### Decision
Use **Railway** for backend deployment.

### Rationale
- **Managed PostgreSQL + Redis** — Railway provides managed Postgres and Redis as add-ons. No need to manually configure RDS + ElastiCache.
- **Docker-based** — Deploy via Dockerfile. Works well with FastAPI's standard Docker image.
- **Simple deployment** — GitHub integration: push to main → auto-deploy. No CI pipeline configuration needed for basic deploys.
- **Cost** — Small-scale deployment fits within Railway's free tier. Scales predictably with usage.

### Consequences
- Less control over infrastructure compared to AWS
- Railway has fewer data center regions than AWS
- For enterprise on-premise (V2.0), a Kubernetes-based alternative will be needed

### Alternatives Rejected
- **AWS (ECS Fargate)** — Operational overhead of setting up VPC, ALB, ECS task definitions, RDS, ElastiCache. Not justified for current scale.
- **Heroku** — No native Docker support (requires container registry workaround). Fewer data center options. Higher cost per dyno.
- **Fly.io** — Good Docker support but no managed Postgres at time of decision. Would need separate Postgres hosting.
