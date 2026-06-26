# REPOSITORY_INVENTORY.md

## Repository Overview
- **Project Name:** AgentForge
- **Description:** AI-powered multi-agent orchestration platform for engineering teams.
- **Tech Stack:**
    - **Frontend:** Next.js 15, Tailwind CSS, Framer Motion, Lucide icons.
    - **Backend:** FastAPI, Python 3.11+.
    - **Agent Orchestration:** LangGraph.
    - **Database:** PostgreSQL with pgvector.
    - **Caching/Rate Limiting:** Redis.
    - **Infrastructure:** Docker, Docker Compose, GitHub Actions.

## File Counts
- **Total Files:** ~338 (tracked)
- **Frontend Files:** 130+ (apps/web)
- **Backend Files:** 120+ (apps/api)
- **Agent System Files:** 17 (apps/api/agents)
- **Memory System Files:** 3 (apps/api/app/memory_service.py, migrations/009, etc.)
- **Analytics Files:** 5 (apps/api/app/routes/analytics.py, migrations/008, 011, 012)
- **Auth Files:** 6 (apps/api/app/auth.py, routes/auth.py, migrations/005, 013)
- **Infrastructure Files:** 6 (Dockerfile, docker-compose.yml, .github/workflows/ci.yml, Makefile)
- **Database Files:** 16 (apps/api/migrations/*.sql, core/database.py)
- **Test Files:** 19 (apps/api/tests/*.py)

## Top 100 Most Important Files (Categorized)

### Core Architecture & Entry Points
1. `apps/api/app/main.py` - Backend entry point.
2. `apps/web/app/page.tsx` - Frontend landing page / "Quick Review" entry.
3. `apps/api/agents/graph.py` - LangGraph workflow definition.
4. `apps/api/agents/orchestrator.py` - Agent execution logic.
5. `apps/api/core/config.py` - Global settings and env vars.
6. `apps/api/core/database.py` - Database pool and migration runner.
7. `apps/api/core/redis.py` - Redis initialization and rate limiting.

### Agent System (Nodes & Prompts)
8. `apps/api/agents/nodes/team_lead_node.py` - Planning and delivery logic.
9. `apps/api/agents/nodes/builder_node.py` - Code generation logic.
10. `apps/api/agents/nodes/reviewer_node.py` - Code review logic.
11. `apps/api/agents/nodes/security_node.py` - Security analysis logic.
12. `apps/api/agents/nodes/tester_node.py` - Test generation logic.
13. `apps/api/agents/nodes/aggregator_node.py` - Results merging logic.
14. `apps/api/agents/prompts/team_lead.jinja2`
15. `apps/api/agents/prompts/builder.jinja2`
16. `apps/api/agents/prompts/reviewer.jinja2`
17. `apps/api/agents/prompts/security.jinja2`

### Core Services
18. `apps/api/app/memory_service.py` - RAG / pgvector memory management.
19. `apps/api/app/file_parser.py` - Repository context ingestion.
20. `apps/api/core/task_tracker.py` - Background task management.
21. `apps/api/app/auth.py` - JWT and password hashing logic.

### API Routes
22. `apps/api/app/routes/tasks.py` - Task lifecycle API.
23. `apps/api/app/routes/executions.py` - Execution status API.
24. `apps/api/app/routes/review.py` - Quick review API.
25. `apps/api/app/routes/projects.py` - Project management API.
26. `apps/api/app/routes/teams.py` - Team/Agent configuration API.
27. `apps/api/app/routes/memories.py` - Memory retrieval API.
28. `apps/api/app/routes/analytics.py` - Execution metrics API.

### Database Migrations
29. `apps/api/migrations/001_initial.sql`
30. `apps/api/migrations/006_projects_and_files.sql`
31. `apps/api/migrations/007_repository_context.sql`
32. `apps/api/migrations/009_memories.sql`

### Frontend Components
33. `apps/web/components/sidebar.tsx`
34. `apps/web/components/QuickReviewTextarea.tsx`
35. `apps/web/components/QuickReviewProgress.tsx`
36. `apps/web/components/QuickReviewResults.tsx`
37. `apps/web/components/agent-network.tsx` - Visualization of agent collaboration.
38. `apps/web/components/execution-graph.tsx` - LangGraph visualizer.
39. `apps/web/components/memory-viewer.tsx`
40. `apps/web/lib/api.ts` - Frontend API client.

## Largest Files
1. `pnpm-lock.yaml` (~3MB)
2. `apps/api/app/routes/projects.py` (21.7KB)
3. `apps/web/app/page.tsx` (17.8KB)
4. `apps/api/app/routes/context.py` (17.1KB)
5. `apps/api/app/routes/review.py` (15.6KB)

## System Architecture Map
- **Frontend (Next.js):** Communicates via REST API to FastAPI.
- **Backend (FastAPI):**
    - **Orchestrator:** Coordinates LangGraph execution.
    - **LangGraph:** Runs agent nodes (Team Lead -> Builder -> [Reviewer, Tester, Security] -> Aggregator -> Team Lead).
    - **Memory Service:** Uses pgvector for long-term storage and retrieval.
    - **Repository Context:** Parses uploaded files and stores chunks for RAG.
- **Data Tier:**
    - **PostgreSQL:** Stores users, projects, teams, tasks, executions, memories (pgvector).
    - **Redis:** Used for global rate limiting.

## Request Lifecycle Map
1. **User Action:** Submits code for "Quick Review" or creates a "Task".
2. **API Layer:**
    - Auth middleware validates JWT (if enabled).
    - Rate limit middleware checks Redis.
    - Request metrics recorded.
3. **Task Creation:**
    - Task record created in Postgres (status: pending).
    - Execution record created.
4. **Execution (Background):**
    - `run_task` triggered.
    - Context fetched (repository chunks + relevant memories).
    - LangGraph initiated with `initial_state`.
5. **Graph Flow:**
    - `team_lead_plan`: Analyzes task and creates a plan.
    - `builder`: Implements code based on plan and context.
    - `fan-out`: Parallel execution of Reviewer, Tester, Security agents.
    - `aggregator`: Merges results from parallel agents.
    - `team_lead_deliver`: Summarizes and finalizes.
6. **Persistence:**
    - Each node update is persisted to `executions.graph_state`.
    - Messages stored in `task_messages`.
    - Final results stored as memories in `agent_memories`.
7. **Client Side:**
    - Frontend polls `/api/v1/tasks/{id}` or listens via WebSocket (if implemented, though polling seems preferred in docs).
    - UI updates in real-time based on `graph_state`.
