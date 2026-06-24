# Glossary

| Term | Definition |
|---|---|
| **Agent** | An AI-powered entity configured with an LLM, system prompt, tools, and memory. Agents can be invoked to perform tasks. |
| **API Key** | A programmatic authentication credential for machine-to-machine access. Stored as SHA-256 hash. |
| **Audit Log** | Immutable record of CRUD operations including actor, action, resource, and timestamp. |
| **Circuit Breaker** | A fault-tolerance pattern that prevents repeated calls to failing services, allowing them time to recover. |
| **Execution** | A single run of an agent or workflow, recording input, output, tokens used, cost, and duration. |
| **JWT** | JSON Web Token — a compact, URL-safe token format used for authentication. |
| **LangGraph** | A framework for building stateful, multi-actor LLM applications as directed graphs. |
| **LLM** | Large Language Model — the underlying AI model (e.g., GPT-4, Claude, Gemini). |
| **Multi-Tenancy** | Architecture where a single instance serves multiple tenants, with data isolation. |
| **OpenTelemetry** | An observability framework for generating, collecting, and exporting telemetry data (traces, metrics, logs). |
| **Prometheus** | An open-source monitoring system with a dimensional data model and query language. |
| **Qdrant** | A vector similarity search engine for storing and querying embeddings. |
| **RAG** | Retrieval-Augmented Generation — enhancing LLM responses with retrieved context from a knowledge base. |
| **Rate Limiting** | Controlling the number of requests a client can make within a time window. |
| **Safe Eval** | An AST-based expression evaluator that prevents arbitrary code execution. |
| **Tenant** | An isolated organizational unit with its own users, agents, workflows, and data. |
| **Tool** | A reusable function that an agent can call (e.g., web search, calculator, API integration). |
| **Turborepo** | A monorepo build system for JavaScript/TypeScript projects. |
| **Vector Store** | A database optimized for storing and searching vector embeddings (Qdrant). |
| **WebSocket** | A protocol for real-time, bidirectional communication between client and server. |
| **Workflow** | A directed graph of nodes (LLM calls, tools, decisions) that defines a multi-step AI process. |
| **Workflow Engine** | A runtime that executes workflow graphs (implemented with LangGraph). |
