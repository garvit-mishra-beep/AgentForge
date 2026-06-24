# ADR-003: PostgreSQL as Primary Database

## Status
Accepted

## Context
AgentForge AI needs to store:

- Structured data: tenants, agents, workflows, API keys, users (with well-defined schemas)
- JSON blobs: model configurations, tool definitions, execution steps (semi-structured)
- Searchable metadata: execution logs, error messages (text search)
- Vector embeddings: agent memory, document chunks (optional, can use pgvector)

## Alternatives Considered

### 1. MongoDB
- **Pros**: Schema-less documents, native JSON, horizontal scaling via sharding, rich query language
- **Cons**: No ACID transactions across collections by default, weaker join performance, larger disk footprint, JSON blobs lose type safety, less mature vector support

### 2. MySQL 8
- **Pros**: ACID compliant, widely deployed, good JSON support
- **Cons**: No native vector support, weaker JSON indexing than PostgreSQL, less advanced indexing features (partial indexes, covering indexes)

### 3. PostgreSQL (Selected)
- **Pros**: Full ACID compliance, excellent JSON/JSONB support with GIN indexes, pgvector extension for embeddings, powerful indexing (B-tree, GiST, GIN, BRIN), mature CTE and window functions, strong ecosystem (PgBouncer, Patroni), excellent async driver (asyncpg)
- **Cons**: Single-node write bottleneck (writes don't scale horizontally without Patroni/Citus), larger memory footprint than SQLite

### 4. SQLite
- **Pros**: Zero configuration, embedded, fast for single-server
- **Cons**: No concurrent writes, no network access, limited concurrency, not suitable for multi-tenant SaaS

## Decision
Use **PostgreSQL 15+** as the primary database.

Key configuration:
- `asyncpg` driver for async I/O
- `pgvector` extension for embedding storage (optional, graceful fallback to JSONB)
- PgBouncer for connection pooling in production
- Weekly `pg_dump` backups, point-in-time recovery enabled

## Consequences

### Positive
- JSONB columns for flexible agent/workflow configurations with indexing
- pgvector allows us to store embeddings in the same database (simpler infrastructure than a separate vector DB for early stages)
- asyncpg provides native async support aligned with FastAPI
- ACID transactions ensure consistency for billing-critical execution records
- Rich indexing strategies for execution log queries (status, time range, tenant)

### Negative
- Vertical scaling ceiling (mitigated by read replicas and Patroni for HA)
- pgvector is less performant than dedicated vector databases at scale (mitigated by using Qdrant for production vector workloads, pgvector for dev/test)
- More operational overhead than managed alternatives (mitigated by using managed PostgreSQL in production)

## Tradeoffs
- We chose PostgreSQL over MongoDB because our data is fundamentally relational (tenants → agents → workflows → executions). JSONB provides the flexibility we need for schema-less agent configs while maintaining relational integrity for core entities.
- We accept pgvector's limitations because for MVP, a single database simplifies operations. We'll migrate vector workloads to Qdrant when scaling demands it.

## References
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/index.html)
- [pgvector](https://github.com/pgvector/pgvector)
- [asyncpg](https://magicstack.github.io/asyncpg/)
