# Deployment Guide — AgentForge

**Last Updated:** June 2026

---

## Architecture

```
┌──────────────────────┐      ┌──────────────────────┐
│   Vercel (Frontend)  │      │  Railway (Backend)   │
│  ┌────────────────┐  │      │  ┌────────────────┐  │
│  │  Next.js 15    │  │◀────▶│  │  FastAPI       │  │
│  │  Edge Network  │  │ HTTP │  │  Docker        │  │
│  └────────────────┘  │  WS  │  └────────────────┘  │
│                      │      │         │             │
│                      │      │  ┌──────┴──────┐      │
│                      │      │  │  PostgreSQL  │      │
│                      │      │  │  + pgvector  │      │
│                      │      │  └─────────────┘      │
│                      │      │         │             │
│                      │      │  ┌──────┴──────┐      │
│                      │      │  │   Redis      │      │
│                      │      │  └─────────────┘      │
└──────────────────────┘      └──────────────────────┘
```

---

## Vercel Setup (Frontend)

### Step 1: Connect GitHub Repository

1. Go to [vercel.com](https://vercel.com) → Add New Project
2. Import the `agentforge` GitHub repository
3. Select the `apps/web` directory as the root (monorepo setup)

### Step 2: Configure Environment Variables

In the Vercel project settings, add:

| Variable | Source |
|----------|--------|
| `NEXT_PUBLIC_APP_URL` | `https://agentforge.vercel.app` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk Dashboard → API Keys |
| `CLERK_SECRET_KEY` | Clerk Dashboard → API Keys |
| `NEXT_PUBLIC_WS_URL` | `wss://api.agentforge.dev/ws` |

### Step 3: Configure Build Settings

From Vercel dashboard:
- **Framework preset:** Next.js
- **Build command:** `cd ../.. && pnpm build --filter=web...` (Turborepo)
- **Output directory:** `.next`
- **Install command:** `pnpm install`

### Step 4: Deploy

Vercel auto-deploys on every push to `main`. Each deploy gets a unique preview URL.

---

## Railway Setup (Backend)

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) → New Project
2. Select "Deploy from GitHub repo" → select `agentforge`
3. Set root directory to `apps/api`

### Step 2: Add Services

From Railway dashboard:

```
Project: agentforge-api
├── FastAPI Service (from apps/api/Dockerfile)
├── PostgreSQL Plugin (v16)
└── Redis Plugin (v7)
```

### Step 3: Configure Environment Variables

In Railway project settings:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway template) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` (Railway template) |
| `OPENAI_API_KEY` | From 1Password |
| `ANTHROPIC_API_KEY` | From 1Password |
| `GOOGLE_API_KEY` | From 1Password |
| `ENCRYPTION_KEY` | Generated 32-byte hex |
| `NODE_ENV` | `production` |

### Step 4: Deploy

Railway auto-deploys on push to `main`. Each deploy creates a new container with the latest Docker image.

---

## GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy AgentForge

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install
      - run: pnpm lint

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: agentforge
          POSTGRES_PASSWORD: agentforge
          POSTGRES_DB: agentforge_test
        ports: [5432:5432]
      redis:
        image: redis:7
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pnpm install
      - run: pnpm test:web
      - run: pnpm test:api
        env:
          DATABASE_URL: postgresql://agentforge:agentforge@localhost:5432/agentforge_test
          REDIS_URL: redis://localhost:6379/0

  deploy-frontend:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: --prod

  deploy-backend:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railway/railway-action@v2
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
```

---

## Environment Promotion

```
dev (local) → staging (railway.dev) → prod (railway.app / vercel.com)
```

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| dev | localhost:3000 | localhost:8000 | Local development |
| staging | *.vercel.app (preview) | *.railway.dev | PR preview, QA |
| prod | agentforge.app | api.agentforge.dev | Production |

---

## Rollback Procedures

### Vercel (Frontend)

1. Go to Vercel dashboard → Deployments
2. Find the last known-good deployment
3. Click "..." → "Promote to Production"
4. Rollback is instant (Vercel serves the previous build)

### Railway (Backend)

1. Go to Railway dashboard → Deployments
2. Find the last known-good deployment
3. Click "Redeploy" on that deployment
4. Railway restarts the service with the previous Docker image

---

## Dockerfile (apps/api)

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
