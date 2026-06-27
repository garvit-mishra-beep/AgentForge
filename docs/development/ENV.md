# Environment Variables — AgentForge

**Last Updated:** June 2026

---

## App Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `NODE_ENV` | Node environment | `development` | Yes |
| `NEXT_PUBLIC_APP_URL` | Frontend URL | `http://localhost:3000` | Yes |
| `API_URL` | Backend URL for BFF routes | `http://localhost:8000` | Yes |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000/ws` | Yes |

## Auth — Clerk

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend API key | `pk_live_xxxxxxxxx` | Yes |
| `CLERK_SECRET_KEY` | Clerk backend secret | `sk_live_xxxxxxxxx` | Yes |
| `CLERK_WEBHOOK_SECRET` | Clerk webhook signing secret | `whsec_xxxxxxxxx` | Yes (webhooks) |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | Custom sign-in path | `/sign-in` | No |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | Custom sign-up path | `/sign-up` | No |

## Database — PostgreSQL

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://user:pass@localhost:5432/agentforge` | Yes |
| `DATABASE_POOL_MIN` | Minimum connection pool size | `2` | No |
| `DATABASE_POOL_MAX` | Maximum connection pool size | `10` | No |

## Redis

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Full Redis connection string | `redis://localhost:6379/0` | Yes |
| `REDIS_JWT_CACHE_TTL` | JWT cache TTL in seconds | `3600` | No |
| `REDIS_RATE_LIMIT_WINDOW` | Rate limit window in seconds | `60` | No |
| `REDIS_RATE_LIMIT_MAX` | Max requests per window | `10` | No |

## AI Providers — OpenAI

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-xxxxxxxxx` | Yes (if using OpenAI models) |
| `OPENAI_API_BASE` | Custom API base URL | `https://api.openai.com/v1` | No |
| `OPENAI_ORG_ID` | OpenAI organization ID | `org-xxxxxxxxx` | No |
| `OPENAI_TIMEOUT` | Request timeout in seconds | `60` | No |

## AI Providers — Anthropic

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-xxxxxxxxx` | Yes (if using Claude models) |
| `ANTHROPIC_API_BASE` | Custom API base URL | `https://api.anthropic.com/v1` | No |
| `ANTHROPIC_TIMEOUT` | Request timeout in seconds | `60` | No |

## AI Providers — Google (Gemini)

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google AI API key | `AIzaxxxxxxxxx` | Yes (if using Gemini models) |
| `GOOGLE_API_BASE` | Custom API base URL | `https://generativelanguage.googleapis.com/v1` | No |
| `GOOGLE_TIMEOUT` | Request timeout in seconds | `60` | No |

## AI Providers — Alibaba (Qwen)

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ALIBABA_API_KEY` | Alibaba Cloud API key | `sk-xxxxxxxxx` | Yes (if using Qwen models) |
| `ALIBABA_API_BASE` | Custom API base URL | `https://dashscope.aliyuncs.com/api/v1` | No |
| `ALIBABA_TIMEOUT` | Request timeout in seconds | `60` | No |

## WebSocket

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `WS_HEARTBEAT_INTERVAL` | Heartbeat ping interval in seconds | `30` | No |
| `WS_MAX_IDLE` | Max idle time before disconnect in seconds | `300` | No |
| `WS_MAX_CONNECTIONS_PER_TASK` | Max concurrent WS connections per task | `10` | No |

## Observability

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `LANGSMITH_API_KEY` | LangSmith tracing API key | `lsv2_xxxxxxxxx` | No |
| `LANGSMITH_PROJECT` | LangSmith project name | `agentforge-dev` | No |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | `http://localhost:4318` | No |
| `SENTRY_DSN` | Sentry error tracking DSN | `https://xxx@xxx.ingest.sentry.io/xxxxx` | No |
| `POSTHOG_API_KEY` | PostHog analytics API key | `phc_xxxxxxxxx` | No |

## Encryption

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ENCRYPTION_KEY` | AES-256 key for API key encryption (32 bytes, hex) | `a1b2c3d4e5f6...` | Yes |

## Example `.env` File

```bash
# App
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxxxxxx
CLERK_SECRET_KEY=sk_live_xxxxxxxxx

# Database
DATABASE_URL=postgresql://agentforge:agentforge@localhost:5432/agentforge

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxx

# Google
GOOGLE_API_KEY=AIzaxxxxxxxxx

# Encryption
ENCRYPTION_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
```

## Important Notes

1. **Never commit `.env` files** — they are in `.gitignore`
2. Copy `.env.example` to `.env` and fill in real values
3. The `ENCRYPTION_KEY` must be exactly 32 bytes (64 hex chars) for AES-256
4. AI provider keys are optional if you don't use that provider's models
5. Railway and Vercel env vars are set via their dashboards, not `.env` files
