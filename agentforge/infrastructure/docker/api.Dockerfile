FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

RUN uv pip install --system --no-cache \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy[asyncio] asyncpg psycopg-binary \
    redis httpx structlog pyjwt passlib[bcrypt] python-dotenv \
    langchain langchain-core langchain-openai langchain-google-genai langchain-anthropic \
    langgraph langgraph-checkpoint langgraph-checkpoint-postgres \
    openai anthropic google-genai \
    qdrant-client

COPY apps/api/ ./apps/api/
COPY packages/ ./packages/

ENV PYTHONPATH=/app
EXPOSE 8000

FROM builder AS runner
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
