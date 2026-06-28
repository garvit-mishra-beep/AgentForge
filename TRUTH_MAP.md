# AgentForge Truth Map

| Claim | Actual Implementation | Status |
|-------|----------------------|--------|
| Multi-Agent Orchestration (LangGraph-powered DAG: Lead → Builder → Reviewer → Deliver) | Implemented in `apps/api/agents/graph.py` with nodes: team_lead_plan, planner, planner_evidence_validation, architect, architect_evidence_validation, builder, builder_evidence_validation, then parallel to reviewer, tester, security (each with evidence validation), aggregator, aggregator_evidence_validation, deployment, deployment_evidence_validation, team_lead_deliver. | Implemented |
| BYOK (Bring Your Own Key) | Implemented via `apps/api/app/routes/keys.py` and encryption service (`apps/api/core/encryption.py`). API keys stored encrypted in `api_keys` table. | Implemented |
| GitHub Native Integration | Implemented in `apps/api/app/integrations/github.py`, `github_enhanced.py`, and routes in `apps/api/app/routes/github.py`. Includes webhook handling, signature verification, and PR reviews. | Implemented |
| Evidence Validation Gate | Implemented via evidence validator node (`apps/api/agents/nodes/evidence_validator_node.py`) and evidence gate core (`app/evidence_gate/core.py`). Integrated into agent workflow as validation nodes. | Implemented |
| Tree-Sitter Intelligence | Not implemented. File parser uses custom Python AST parser for Python and regex-based generic parser for other languages (`apps/api/app/file_parser.py`). No tree-sitter integration found. | Missing |
| Secure Sandbox Execution | Implemented via sandbox executor (`apps/api/app/services/sandbox_executor.py`) using Docker with resource limits and security options. | Implemented |
| Vector Memory | Not implemented. Memory service (`apps/api/app/memory_service.py`) uses keyword-based ILIKE search for retrieval, not vector embeddings. | Missing |
| Local Auth (JWT + bcrypt) | Implemented in `apps/api/app/auth.py` with JWT access/refresh tokens and bcrypt password hashing. | Implemented |
| Prometheus Metrics | Implemented via `/api/v1/metrics` endpoint in `apps/api/app/main.py` and observability module (`apps/api/core/observability.py`). | Implemented |
| Real-time Streaming | Not implemented. No WebSocket or Server-Sent Event endpoints found in codebase. Archive references indicate planned feature (DX-7). | Missing |
| Enterprise SSO / RBAC | Not implemented. Auth system is local JWT-based only. No role-based access control or SSO integration found. README marks as planned. | Missing |
| Backend Environment Setup Documentation | README incorrectly instructed users to copy `.env.example` from parent directory (`cp ../.env.example .env`) when the template was actually in the repository root after my fix. Corrected to show proper copy command and added clarification about file locations. | Fixed |
| Environment Variable Completeness | The `.env.example` in the repository root now documents ALL variables across the entire monorepo (both frontend and backend) with clear section headers, whereas previously only backend variables were documented in `apps/api/.env.example`. | Fixed |