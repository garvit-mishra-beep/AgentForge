# Setup Guide — AgentForge

**Last Updated:** June 2026

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Node.js | 20.x LTS | Next.js frontend + Turborepo |
| Python | 3.11+ | FastAPI backend + LangGraph |
| Docker Desktop | 24+ | PostgreSQL 16 + Redis 7 local infrastructure |
| pnpm | 9.x | Package manager (workspaces) |

### Verify Prerequisites

```bash
node --version   # v20.x.x
python --version # Python 3.11.x
docker --version # Docker version 24.x.x
pnpm --version   # 9.x.x
```

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/agentforge/agentforge.git
cd agentforge
```

---

## Step 2: Install Dependencies

```bash
# Install all workspace dependencies (apps/web, apps/api, packages/*)
pnpm install
```

This runs `pnpm install` in the root, which installs dependencies for all workspaces defined in `pnpm-workspace.yaml`.

---

## Step 3: Configure Environment Variables

```bash
# Root environment (frontend-facing variables)
cp .env.example .env

# Backend environment
cp apps/api/.env.example apps/api/.env
```

Edit both `.env` files with real values. See [ENV.md](ENV.md) for the full variable reference.

**Minimum required variables for local development:**

In `.env`:
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<your_clerk_publishable_key>
CLERK_SECRET_KEY=<your_clerk_secret_key>
```

In `apps/api/.env`:
```
DATABASE_URL=postgresql://agentforge:agentforge@localhost:5432/agentforge
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=<your_openai_key>
ANTHROPIC_API_KEY=<your_anthropic_key>
GOOGLE_API_KEY=<your_google_key>
ENCRYPTION_KEY=<32_bytes_hex>
```

---

## Step 4: Start Infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL 16** on port `5432` (database: `agentforge`, user: `agentforge`, password: `agentforge`)
- **Redis 7** on port `6379`

Verify:
```bash
docker compose ps
# Both containers should show "Up" status
```

---

## Step 5: Run Database Migrations

```bash
pnpm db:migrate
```

This applies all Prisma migrations in `packages/db/migrations/` to the local PostgreSQL instance.

---

## Step 6: Seed Sample Data

```bash
pnpm db:seed
```

Creates:
- 1 demo user
- 1 demo project ("My Project")
- 1 demo team with 3 agents (Team Lead → Gemini 1.5 Pro, Backend → Claude Sonnet, Reviewer → GPT-4o)
- 1 sample completed task

---

## Step 7: Start Development Servers

```bash
pnpm dev
```

This runs both servers concurrently via Turborepo:
- **Frontend:** Next.js on [http://localhost:3000](http://localhost:3000)
- **Backend:** FastAPI on [http://localhost:8000](http://localhost:8000)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Verifying the Setup

1. Open [http://localhost:3000](http://localhost:3000) — you should see the sign-in page
2. Sign in via Clerk (use the demo credentials or create a new account)
3. You should see the dashboard with the seeded project
4. Open [http://localhost:8000/docs](http://localhost:8000/docs) — you should see the OpenAPI documentation
5. Try `GET /api/v1/health` — should return `{"status": "ok"}`

---

## Running Individual Servers

```bash
# Frontend only
pnpm dev:web

# Backend only
pnpm dev:api

# All packages in watch mode
pnpm dev:packages
```

---

## Common Issues & Fixes

### Issue 1: `pnpm install` fails with "ERR_PNPM_OUTDATED_LOCK_FILE"

```bash
# Regenerate lock file
pnpm install --frozen-lockfile false
pnpm install
```

### Issue 2: Docker containers fail to start on port conflict

```bash
# Check what's using the port
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Stop conflicting services or change docker-compose.yml ports
# Then restart
docker compose down
docker compose up -d
```

### Issue 3: Database connection refused

```bash
# Verify PostgreSQL is running
docker compose ps

# If not running, check logs
docker compose logs postgres

# Restart if needed
docker compose restart postgres

# Wait 5 seconds for PostgreSQL to initialize, then try again
```

### Issue 4: Clerk authentication errors

```bash
# Ensure both .env files have correct Clerk keys
# The publishable key starts with "pk_" and the secret key starts with "sk_"
# Verify they match the keys in your Clerk dashboard at https://dashboard.clerk.com
```

### Issue 5: AI provider API errors

```bash
# Check that API keys are set in apps/api/.env
# Verify key format:
#   OpenAI: sk-proj-...
#   Anthropic: sk-ant-...
#   Google: AIza...
# Test with:
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```
