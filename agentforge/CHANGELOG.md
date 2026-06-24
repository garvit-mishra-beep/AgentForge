# Changelog

All notable changes to AgentForge AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-25

### Added

#### Core Platform
- FastAPI async backend with multi-tenant architecture
- User authentication with JWT (access + refresh tokens)
- API key authentication with SHA-256 hashing
- Agent CRUD and invocation with LLM provider abstraction
- Workflow CRUD and execution with LangGraph-based engine
- RAG pipeline: document ingestion, vector search, LLM-augmented generation
- WebSocket support for real-time execution streaming
- PostgreSQL database with SQLAlchemy 2.0 async ORM
- Redis integration for caching and WebSocket pub/sub
- Qdrant vector store for semantic search

#### Security
- JWT token validation (HS256, audience, issuer, expiry, jti)
- Password hashing with bcrypt (per-password salt)
- Tenant isolation at query level (tenant_id filtering)
- Rate limiting (auth token, register, upload endpoints)
- Audit logging for all CRUD operations
- Safe expression evaluation (AST-based, prevents code injection)
- File upload validation (MIME type, size limits)
- Secret validation at application startup
- CORS middleware with configurable origins

#### Observability
- Prometheus metrics: HTTP requests, workflows, agents, RAG, tokens
- OpenTelemetry distributed tracing (FastAPI, HTTPX, SQLAlchemy)
- Structured logging via structlog (JSON or console)
- Health check endpoints: liveness, readiness, full health
- Circuit breakers for LLM, Qdrant, Redis (pybreaker)
- Retry policies with exponential backoff (tenacity)

#### Data Layer
- Alembic migrations (async-compatible)
- Database connection pooling (pool_size=20, max_overflow=10)
- Lazy vector store initialization (Qdrant client on first use)

#### Testing
- 130 tests across security, integration, observability, and API
- 76% backend code coverage
- Mock database sessions for unit tests
- Tenant isolation, rate limiting, and audit logging test coverage

#### Documentation
- Setup guide, local development, deployment
- Architecture and system design documentation
- API reference with all endpoints
- Observability, security, testing guides
- Troubleshooting, roadmap, glossary
- Operations runbook with incident response procedures
- Production checklist
- Docker validation guide

#### Infrastructure
- Docker Compose for local development (PostgreSQL, Redis, Qdrant, API, Web)
- Dockerfiles for API and Web services
- Health checks in Docker Compose
- GitHub Actions CI workflow
- Turborepo monorepo configuration

#### Community
- CONTRIBUTING.md with coding standards, commit conventions, PR workflow
- SECURITY.md with vulnerability reporting policy
- Code of Conduct (Contributor Covenant)
- Issue templates (bug, feature, documentation, security)
- Pull request template
- Funding configuration

### Known Issues
- Rate limiting uses in-memory store (resets on process restart, not suitable for multi-replica)
- WebSocket authentication is minimal
- Qdrant client version check warning in development (harmless)
