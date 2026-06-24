# Root Dockerfile for monorepo builds
FROM python:3.12-slim AS api-builder

WORKDIR /app

RUN pip install uv
RUN uv pip install --system --no-cache \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy[asyncio] asyncpg psycopg-binary \
    redis httpx structlog pyjwt passlib[bcrypt] python-dotenv \
    langchain langchain-core langchain-openai langchain-google-genai langchain-anthropic \
    langgraph langgraph-checkpoint langgraph-checkpoint-postgres \
    openai anthropic google-genai qdrant-client

COPY apps/api/ ./apps/api/
COPY packages/ ./packages/
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:20-alpine AS web-builder

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./apps/web/
RUN cd apps/web && npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN cd apps/web && npm run build

FROM node:20-alpine AS web-runner
WORKDIR /app
COPY --from=web-builder /app/apps/web/.next/standalone ./apps/web/
COPY --from=web-builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=web-builder /app/apps/web/public ./apps/web/public
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
