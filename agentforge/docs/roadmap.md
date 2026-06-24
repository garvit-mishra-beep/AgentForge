# Roadmap

## Current Release: v0.1.0 (Pre-Alpha)

### ✅ Completed

**Core Platform**
- FastAPI async backend with multi-tenancy
- User authentication (JWT + API keys)
- Agent CRUD and invocation
- Workflow CRUD and execution
- RAG pipeline (ingest, search, augment)
- WebSocket real-time streaming

**Security**
- JWT with HS256, audience/issuer validation
- Password hashing with bcrypt
- API key authentication
- Tenant isolation at query level
- Rate limiting (token, register, upload)
- Audit logging (CRUD operations)
- Safe expression evaluation (AST-based)
- Upload validation (MIME type, size limits)
- Secret validation at startup

**Observability**
- Prometheus metrics (HTTP, workflows, agents, RAG, tokens)
- OpenTelemetry distributed tracing (FastAPI, HTTPX, SQLAlchemy)
- Structured logging (structlog, JSON format)
- Health checks (database, Redis, Qdrant)
- Circuit breakers (LLM, Qdrant, Redis)
- Retry with exponential backoff

**Data Layer**
- SQLAlchemy 2.0 async ORM
- PostgreSQL with connection pooling
- Redis caching and pub/sub
- Qdrant vector store
- Alembic migrations (async-compatible)

**Configuration**
- Pydantic Settings with env file support
- CORS configuration
- Upload size and MIME type limits
- Configurable timeouts per service
- Auto-migration on startup

### 🔄 In Progress (v0.2.0)

- Grafana dashboards for API, Workflow, RAG, Infrastructure
- SLO framework and error budgets
- Operations runbook with incident response procedures
- Chaos testing for resilience verification
- Coverage improvement to 80%+

### 📋 Planned (v0.3.0 - v1.0.0)

**Short-term (v0.3.0)**
- Integration tests with real containerized services
- Performance benchmarking and optimization
- API versioning strategy
- OpenAPI specification export improvements
- Docker Compose production profile

**Medium-term (v0.4.0 - v0.5.0)**
- Rate limiting with Redis backend (distributed)
- WebSocket authentication improvements
- Admin dashboard for tenant management
- Usage billing and quotas
- API documentation portal

**Long-term (v1.0.0)**
- Horizontal scaling guides
- Multi-region deployment
- Enterprise SSO (SAML/OIDC)
- Audit log retention policies
- Compliance certifications preparation

### 🚀 Future Exploration

- Agent evaluation framework
- Fine-tuning integration
- Model A/B testing
- Advanced RAG strategies (HyDE, multi-query, reranking)
- LangSmith integration
- CLI tool for agent management

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **Major** (1.x): Breaking changes to public API
- **Minor** (x.1): New features, backward compatible
- **Patch** (x.x.1): Bug fixes, performance improvements
