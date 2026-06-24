# ADR-002: FastAPI for Backend API

## Status
Accepted

## Context
AgentForge AI requires a backend framework that supports:

- High-concurrency I/O (many simultaneous agent executions)
- Real-time streaming (SSE for agent token-by-token output)
- WebSocket connections (for live workflow execution updates)
- Rich API documentation (for developer experience)
- Python ecosystem (LangGraph, LangChain, ML libraries)

## Alternatives Considered

### 1. Django + Django REST Framework
- **Pros**: Mature, batteries-included, great ORM, admin interface
- **Cons**: Synchronous by default (needs Channels for async), heavy, slower request throughput, template engine overhead

### 2. Flask
- **Pros**: Lightweight, simple, vast ecosystem
- **Cons**: Synchronous, no built-in async support, requires extensions for everything, no automatic OpenAPI docs

### 3. Starlette (Pure)
- **Pros**: Lightweight, async-native, high performance
- **Cons**: No built-in data validation, no auto-docs, more manual boilerplate

### 4. FastAPI (Selected)
- **Pros**: Async-native, automatic OpenAPI docs, Pydantic validation, high performance (on par with Node.js/Go), built-in WebSocket support, SSE support via StreamingResponse, huge ecosystem alignment with LangChain/LangGraph
- **Cons**: Younger ecosystem than Django, async SQLAlchemy has quirks, fewer "batteries" (no admin panel, no built-in auth)

## Decision
Use **FastAPI** as the backend framework.

Key dependencies:
- `fastapi` — framework
- `uvicorn[standard]` — ASGI server
- `pydantic` / `pydantic-settings` — validation and config
- `sqlalchemy[asyncio]` + `asyncpg` — async database
- `langgraph` — workflow engine (native Python integration)

## Consequences

### Positive
- Automatic OpenAPI 3.1 docs at `/docs` and `/redoc`
- Pydantic validation ensures type safety at API boundaries
- Native async support handles concurrent agent executions efficiently
- Streaming responses work naturally with `StreamingResponse`
- WebSocket support is built-in, not an add-on
- Direct Python integration with LangGraph, LangChain, and ML libraries

### Negative
- SQLAlchemy async requires careful session management
- No built-in admin interface (we'll build a limited one or skip)

## Tradeoffs
- Django was rejected despite its maturity because AgentForge AI is I/O-bound, not CPU-bound, and needs async from day one. Adding async to Django is possible but adds complexity.
- The lack of batteries (admin, auth) is acceptable because our frontend is a separate Next.js app, and auth is handled by Clerk.

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [LangGraph Python API](https://langchain-ai.github.io/langgraph/)
