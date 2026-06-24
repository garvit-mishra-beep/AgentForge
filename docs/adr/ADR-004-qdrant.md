# ADR-004: Qdrant for Vector Database

## Status
Accepted

## Context
AgentForge AI requires vector storage for:

- **Long-term memory**: Store agent conversation summaries and recall semantically similar past interactions
- **RAG (Retrieval-Augmented Generation)**: Index document chunks and retrieve relevant context at query time
- **Semantic caching**: Cache LLM responses based on embedding similarity
- **User memory**: Store and retrieve user-specific facts and preferences

## Alternatives Considered

### 1. Pinecone (Managed)
- **Pros**: Fully managed, no ops overhead, high performance, good SDK
- **Cons**: Vendor lock-in, egress costs, no self-hosting option, expensive at scale, data residency concerns

### 2. Weaviate
- **Pros**: Open source, hybrid search (vector + keyword), built-in modules (NER, summarization), GraphQL API
- **Cons**: Heavier deployment (more resource intensive), GraphQL-only API is overkill for simple vector ops, complex configuration

### 3. pgvector (PostgreSQL Extension)
- **Pros**: No additional infrastructure, stays within PostgreSQL ecosystem, good enough for small to medium scale
- **Cons**: Performance degrades at scale (sequential scan for high-dimensional vectors without index), no advanced features (filters, hybrid search, multi-tenancy isolation), limited index types (IVFFlat, HNSW)

### 4. Qdrant (Selected)
- **Pros**: Open source (Apache 2.0), self-hostable or managed, gRPC API for high performance, rich filtering (geo, payload, multi-tenant isolation), HNSW index by default, optimized for production workloads, low resource footprint, excellent Docker support
- **Cons**: Smaller community than Pinecone/Weaviate, no built-in hybrid search (requires separate keyword index), no pre-built ML modules

### 5. Chroma
- **Pros**: Simple, Python-native, easy to embed
- **Cons**: Not production-ready, no native gRPC, no multi-tenancy, no filtering capabilities

## Decision
Use **Qdrant** as the vector database.

Key configuration:
- Docker deployment for development, managed Qdrant Cloud for production
- gRPC API for client communication
- HNSW index with payload filtering for multi-tenant isolation
- Collection per tenant for data isolation

## Consequences

### Positive
- Self-hostable (Apache 2.0 license) — no vendor lock-in for core infrastructure
- gRPC API provides excellent performance (2-5x faster than REST for vector operations)
- Rich filtering enables multi-tenant isolation at the database level
- HNSW index provides high recall with reasonable memory usage
- Low resource footprint (256MB RAM minimum for small collections)
- Managed option (Qdrant Cloud) available when we don't want to self-host

### Negative
- Additional infrastructure component to manage (mitigated by using Qdrant Cloud in production)
- No built-in hybrid search — we implement separate BM25 keyword search
- No built-in ML modules — embedding generation happens in our application layer

## Tradeoffs
- We chose Qdrant over Pinecone because we want self-hosting capability for enterprise customers and data residency requirements. The cost savings at scale are also significant.
- We chose Qdrant over pgvector because we anticipate vector-heavy workloads (memory, RAG) that would degrade PostgreSQL performance. Qdrant handles vector operations natively without competing for database resources.
- We accept the additional infrastructure complexity because vector storage is central to our platform's value proposition (memory and RAG).

## References
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant vs Pinecone vs Weaviate](https://qdrant.tech/blog/qdrant-vs-pinecone-vs-weaviate/)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
