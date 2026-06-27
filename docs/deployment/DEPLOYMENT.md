# Deployment Guide — AgentForge

Detailed specifications for deploying the Next.js frontend to Vercel and the FastAPI backend service to Railway or Docker-compatible hosting solutions.

---

## 1. System Architecture Diagram

```text
┌──────────────────────┐      ┌──────────────────────┐
│   Vercel (Frontend)  │      │  Railway (Backend)   │
│  ┌────────────────┐  │      │  ┌────────────────┐  │
│  │  Next.js 15    │  │◀────＞│  │  FastAPI       │  │
│  │  Edge Network  │  │ HTTP  │  │  Docker        │  │
│  └────────────────┘  │  WS   │  └────────────────┘  │
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

## 2. Vercel Setup (Frontend client)

### Step 1: Create Project
1. Log in to [vercel.com](https://vercel.com) and click **Add New Project**.
2. Connect your GitHub repository and select the subfolder `apps/web` as the project root.

### Step 2: Configure Environment Variables
Configure these variables in your Vercel settings page:

| Variable | Recommended Value | Description |
|:---|:---|:---|
| `NEXT_PUBLIC_APP_URL` | `https://agentforge.vercel.app` | The public client URL. |
| `NEXT_PUBLIC_API_URL` | `https://api.agentforge.dev` | The REST API backend URL. |
| `NEXT_PUBLIC_WS_URL` | `wss://api.agentforge.dev` | The WebSocket event stream URL. |

---

## 3. Railway Setup (Backend API)

### Step 1: Add PostgreSQL and Redis
Ensure your project contains:
1. A PostgreSQL service (running PostgreSQL 16 or newer) with the `pgvector` extension enabled.
2. A Redis service (running Redis 7 or newer).

### Step 2: Configure Environment Variables
Add these values in your backend service configuration:

| Variable | Source / Recommended Value | Description |
|:---|:---|:---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | PostgreSQL connection string. |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Redis connection string. |
| `JWT_SECRET` | 32-byte secure key | Secret key used to sign session tokens. |
| `ENCRYPTION_KEY` | 32-byte secure key | Fernet key used to encrypt BYOK values. |
| `OPENAI_API_KEY` | From credentials vault | Default fallback OpenAI API key. |

---

## 4. Docker Deployment

The backend service can be built and run using the root Dockerfile configuration:

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
