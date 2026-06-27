# Product Requirements Document (PRD) — AgentForge

This document maps out the core product requirements, vision, user scenarios, and target capabilities of the AgentForge AI Development OS V1.

---

## 1. Product Vision

AgentForge replaces the single-prompt AI coding pattern with a coordinated, specialized team of AI agents (Team Lead, Planner, Architect, Builder, Tester, Reviewer, and Deployment). Each agent operates with a focused system prompt, model configuration, and isolated operational boundary. The results are high-fidelity, verified code changes with built-in evaluation gates and complete audit trails.

---

## 2. Core Implemented Features (V1 Release Candidate)

| Feature Component | Description | Implementation Status |
|:---|:---|:---:|
| **Multi-Agent Engine** | LangGraph orchestration routing states sequentially and in parallel through specialized agent nodes. | ✅ Implemented |
| **Local JWT Authentication** | BCrypt password hashing, session tokens, refresh tokens, and tenant-isolated security gates. | ✅ Implemented |
| **BYOK (Bring Your Own Key)** | Dynamic API credential resolution hierarchy (Project → User → Global). | ✅ Implemented |
| **Vector Memory Service** | pgvector-based PostgreSQL database semantic search for retrieving design patterns and decisions. | ✅ Implemented |
| **Workspace clients** | Next.js visual dashboard, Click Python CLI script, and FastAPI gateway service. | ✅ Implemented |
| **Evidence Validation Gate** | Automated checks verifying syntax compilation and test suite correctness. | ✅ Implemented |

---

## 3. Product Workflows & Capabilities

### Complete Task Execution Flow
1. **Requirements Analysis:** The user submits a task (e.g., "Add JWT validation"). The Team Lead analyzes the prompt and creates a plan.
2. **Planning:** The Planner breaks the requirements into a detailed, structured execution plan.
3. **Architecture:** The Architect audits design patterns for system quality.
4. **Code Generation:** The Builder writes source files and database migrations.
5. **Quality Verification:** The Tester, Reviewer, and Security agents run in parallel to generate tests, verify styling, and flag security gaps.
6. **Delivery:** The Team Lead aggregates the validated files and delivers them to the user for final approval.

---

## 4. Planned Capabilities (Future Roadmap)

* **Enterprise workspaces:** Organization directories, multi-tenant billing models, and role-based workspace sharing (SSO).
* **Codebase indexing:** Deeper Tree-Sitter support to build complete symbol indexes and call graphs across large multi-language packages.
* **Custom Agent Roles:** Interface allowing developers to create custom agents with dedicated system prompts and tool access.
