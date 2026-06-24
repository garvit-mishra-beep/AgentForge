# ADR-005: LangGraph for Workflow Engine

## Status
Accepted

## Context
AgentForge AI needs to execute multi-step agent workflows with:

- Sequential execution (Agent A → Agent B → Agent C)
- Conditional branching (if/then/else based on agent output)
- Parallel execution (multiple agents simultaneously)
- Looping (retry, refine until condition met)
- Checkpointing (resume from failure, pause/resume)
- Human-in-the-loop (approval gates)
- State management across steps

## Alternatives Considered

### 1. Temporal.io
- **Pros**: Battle-tested, durable execution, built-in retries, saga patterns, activity timeouts
- **Cons**: Heavy operational overhead (Temporal Server cluster), SDK complexity, overkill for agent-focused workflows, long-poll based (not real-time), Python SDK less mature

### 2. Airflow / Prefect
- **Pros**: Mature DAG execution, scheduling, rich UI
- **Cons**: Designed for batch data pipelines, not real-time agent execution, no native support for LLM patterns, heavy for agent use cases

### 3. Custom State Machine
- **Pros**: Full control, no external dependency, can optimize for exact use case
- **Cons**: Building and maintaining graph execution engine is non-trivial, edge cases in conditional routing, no checkpointing, no visual debugging

### 4. LangGraph (Selected)
- **Pros**: Purpose-built for agent workflows, native support for StateGraph patterns, checkpointing built-in (PostgreSQL, memory, or file), conditional and parallel edges, human-in-the-loop support, streaming state updates, Python-native, LangChain ecosystem integration, active development by LangChain team, excellent documentation with agent examples
- **Cons**: Relatively new (less battle-tested than Temporal), Python-only (future multi-language support uncertain), tied to LangChain ecosystem

### 5. CrewAI
- **Pros**: Simple role-based agent orchestration, good for small teams of agents
- **Cons**: Less flexible than LangGraph for complex workflows, no checkpointing, limited conditional logic, younger project

## Decision
Use **LangGraph** as the workflow engine.

Key integration:
- `StateGraph` with typed `AgentState` for type-safe state management
- `AsyncPostgresSaver` checkpointer for production persistence
- Streaming via `.astream_events()` for real-time UI updates
- Conditional edges for branching logic
- Human-in-the-loop via `interrupt()` for approval gates

## Consequences

### Positive
- Purpose-built for agent workflows with native LLM patterns
- Checkpointing enables resume-from-failure, pause/resume, and debugging
- Streaming state updates enable real-time workflow visualization in the frontend
- Conditional edges handle branching, looping, and retry logic naturally
- Python integration is seamless with FastAPI backend
- Active community and rapid development

### Negative
- LangGraph API is evolving and may have breaking changes (mitigated by pinning versions)
- Python-only limits our ability to offer multi-language SDKs in the future
- Heavy dependency on LangChain ecosystem (some transitive dependencies)

### Tradeoffs
- LangGraph was chosen over Temporal because it's purpose-built for agents. Temporal excels at generic durable execution but lacks agent-native patterns (LLM streaming, tool calling, state graph).
- LangGraph was chosen over a custom state machine because building graph execution, checkpointing, and streaming from scratch would take months and would never match LangGraph's quality.
- The dependency on LangChain is acceptable because LangGraph's benefits outweigh the coupling risk. If needed, we can implement custom nodes that don't use LangChain.

## References
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Concepts: State Graphs](https://langchain-ai.github.io/langgraph/concepts/high_level/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
