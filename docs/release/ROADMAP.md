# Release Roadmap — AgentForge

A timeline of active capabilities and scheduled milestones for AgentForge development.

---

## 1. Version Timeline

```text
  v0.1.0 ────► v0.3.0 ────► v1.0.0-rc1 ────► v1.5.0 (Q3) ────► v2.0.0 (Q4)
 Scaffold    Streaming      BYOK & Local     Workspace         Enterprise
 Foundation   Events        JWT Auth         SSO & Invites      SAML & Audit
```

---

## 2. Release Milestones

### Milestone 1: Foundation (v0.1.0 - v0.3.0) — ✅ Complete
* Scaffolded monorepo using Turborepo (Next.js client + FastAPI backend).
* Constructed initial LangGraph state machine structure.
* Implemented real-time execution event streaming using WebSockets and Redis Pub/Sub channels.

### Milestone 2: Release Candidate (v1.0.0-rc1) — ✅ Active (Current)
* **Local Security and Isolation:** Replaced external authentication APIs with a local PyJWT bcrypt-secured token/refresh service.
* **BYOK Credentials:** Implemented layered credential loading (Project → User → System Global).
* **Robust Orchestration:** Standardized agent node configurations, individual execution timeouts, and error handling behaviors.
* **Unified Documentation Vault:** Professional repository layout reorganization.

### Milestone 3: Team Workspaces (v1.5.0) — 📋 Scheduled (Q3 2026)
* **Collaborative Spaces:** Shared workspaces allowing teams to invite members, share projects, and review task execution reports.
* **Local Code Indexing:** Integration of a local Tree-Sitter parsing daemon to cache symbol call graphs and minimize agent context sizes.
* **Interactive Diff Editor:** visual code editor inside the web client allowing developers to edit code suggestions directly before clicking Approve.

### Milestone 4: Enterprise Compliance (v2.0.0) — 📋 Scheduled (Q4 2026)
* **SAML Single Sign-On (SSO):** Corporate sign-on integration.
* **Audit Logging:** Implemented structured, immutable logs recording prompt history, decrypted key access, and code commits for compliance.
* **Custom Agent Builder:** Custom templates and prompts configuration panel.
