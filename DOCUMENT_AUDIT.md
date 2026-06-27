# Document Audit — AgentForge

A comprehensive audit of every markdown file in the repository to clean up documentation noise, resolve duplicates, identify stale plans, and build a unified release candidate documentation library.

---

## 1. Classification Categories

* **✅ Active**: Relevant, correct, and matches codebase reality.
* **⚠️ Outdated**: Contains useful info but does not align with the current implementation. Needs updates.
* **👯 Duplicate**: Content is covered better or more thoroughly in another document.
* **🗄️ Archive Candidate**: Historical value (planning specs, audits, assessments) but no longer reflects active architecture. To be moved to `docs/archive/`.
* **🗑️ Delete Candidate**: Empty or pure noise.

---

## 2. Global Document Registry

### Root Directory

| Document | Classification | Target Action |
|:---|:---:|:---|
| `README.md` | **✅ Active** | Rewrite root landing page README. |
| `REPOSITORY_MAP.md` | **✅ Active** | Refreshed repository layout. |
| `AGENTS.md` | **✅ Active** | Keep at root as it is a critical system benchmark/config rule. |
| `AGENTFORGE_V1_MASTER_ASSESSMENT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `AGENT_QUALITY_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `AGENT_SYSTEM_GAP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `AI_DEVELOPMENT_OS_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `BYOK_ARCHITECTURE_PLAN.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `CODE_QUALITY_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `COMPETITIVE_ADVANTAGE_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `COMPETITIVE_ANALYSIS_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `DEPLOYMENT_READINESS_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `DEVELOPER_EXPERIENCE_GAP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `DEVELOPMENT_MEMORY_GAP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `EXECUTION_SANDBOX_SUMMARY.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `FEATURE_TRUTH_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `FOUNDER_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `GITHUB_INTEGRATION_GAP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `GITHUB_WORKFLOW_SUMMARY.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `IMPLEMENTATION_COMPLETE_SUMMARY.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `NEXT_90_DAY_EXECUTION_PLAN.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `PERFORMANCE_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `REPOSITORY_CLEANUP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `REPOSITORY_INTELLIGENCE_GAP_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `REPOSITORY_INTELLIGENCE_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `SANDBOX_SECURITY.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `SECURITY_AUDIT_REPORT.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |
| `V1_REMAINING_ROADMAP.md` | **🗄️ Archive** | Move to `docs/archive/reports/` |

---

### `apps/` Directory

| Document | Classification | Target Action |
|:---|:---:|:---|
| `apps/README.md` | **✅ Active** | Rewrite for apps workspace tree. |
| `apps/api/README.md` | **✅ Active** | Rewrite backend setup + endpoints doc. |
| `apps/api/BENCHMARK_README.md` | **✅ Active** | Keep/consolidate. |
| `apps/api/tests/README.md` | **👯 Duplicate** | Archive. Coverage inside `docs/development/TESTING.md`. |
| `apps/web/README.md` | **✅ Active** | Rewrite Next.js setup doc. |
| `apps/cli/README.md` | **✅ Active** | Rewrite Python CLI setup doc. |

---

### `docs/` Core Directory

| Document | Classification | Target Action |
|:---|:---:|:---|
| `docs/README.md` | **✅ Active** | Rewrite primary landing README. |
| `docs/CHANGELOG.md` | **✅ Active** | Relocate to root `CHANGELOG.md` for standards. |
| `docs/TERMS_OF_USE.md` | **✅ Active** | Relocate to root `TERMS_OF_USE.md`. |
| `docs/DOCUMENTATION_INDEX.md` | **✅ Active** | Refresh index after directory organization. |
| `docs/api/README.md` | **👯 Duplicate** | Delete (covered by docs/api/API.md). |
| `docs/api/API.md` | **✅ Active** | Rename & rewrite to `docs/api/API_REFERENCE.md`. |
| `docs/architecture/README.md` | **👯 Duplicate** | Delete. |
| `docs/architecture/SYSTEM_ARCHITECTURE.md`| **✅ Active** | Rewrite with Mermaid diagrams matching reality. |
| `docs/architecture/TECH_SPEC.md` | **✅ Active** | Keep spec. |
| `docs/architecture/SCHEMA.md` | **✅ Active** | Keep database structures. |
| `docs/architecture/AGENT_ROLES.md` | **👯 Duplicate** | Consolidate with `docs/agents/AGENT_SYSTEM.md`. |
| `docs/architecture/AGENT_PROMPTS.md` | **👯 Duplicate** | Consolidate with `docs/agents/AGENT_SYSTEM.md`. |
| `docs/architecture/PROMPTS.md` | **👯 Duplicate** | Consolidate with `docs/agents/AGENT_SYSTEM.md`. |
| `docs/architecture/AGENT_MEMORY.md` | **👯 Duplicate** | Consolidate with `docs/agents/AGENT_SYSTEM.md`. |
| `docs/architecture/MODEL_REGISTRY.md` | **⚠️ Outdated** | Update to reflect user-BYOK model chains. |
| `docs/architecture/HALLUCINATION_GUARD.md`| **✅ Active** | Keep security guard specs. |
| `docs/development/README.md` | **👯 Duplicate** | Delete. |
| `docs/development/ONBOARDING.md` | **✅ Active** | Move/merge into `docs/getting-started/ONBOARDING.md`. |
| `docs/development/SETUP.md` | **✅ Active** | Rewrite with real local stack configurations. |
| `docs/development/TESTING.md` | **✅ Active** | Update testing strategies and sandbox guides. |
| `docs/development/CONVENTIONS.md` | **✅ Active** | Keep styling conventions. |
| `docs/development/DX.md` | **✅ Active** | Keep dev experience specs. |
| `docs/development/ENV.md` | **👯 Duplicate** | Consolidate into `SETUP.md`. |
| `docs/development/PERFORMANCE.md` | **✅ Active** | Keep perf rules. |
| `docs/development/OBSERVABILITY.md` | **✅ Active** | Keep monitoring metrics details. |
| `docs/development/DECISIONS.md` | **✅ Active** | Keep ADR (Architecture Decision Record). |
| `docs/development/FAQ.md` | **✅ Active** | Keep FAQ. |
| `docs/development/GLOSSARY.md` | **✅ Active** | Keep glossary. |
| `docs/development/CONTRIBUTING.md` | **✅ Active** | Relocate to root `CONTRIBUTING.md`. |
| `docs/development/CLAUDE.md` | **✅ Active** | Keep IDE helper instructions. |
| `docs/development/AUDIT.md` | **🗄️ Archive** | Move to `docs/archive/` |
| `docs/development/BUGS.md` | **🗄️ Archive** | Move to `docs/archive/` |
| `docs/development/CLEANUP_PLAN_*.md` | **🗄️ Archive** | Move to `docs/archive/` |
| `docs/deployment/README.md` | **👯 Duplicate** | Delete. |
| `docs/deployment/DEPLOYMENT.md` | **✅ Active** | Update deployment checklist. |
| `docs/security/README.md` | **👯 Duplicate** | Delete. |
| `docs/security/SECURITY.md` | **✅ Active** | Relocate to root `SECURITY.md`. |
| `docs/security/SECURITY_MODEL.md` | **✅ Active** | Keep detailed threat model parameters. |
| `docs/security/INCIDENT_RUNBOOK.md` | **✅ Active** | Keep runbook. |
| `docs/security/DATA_PRIVACY.md` | **✅ Active** | Keep data privacy specifications. |
| `docs/product/README.md` | **👯 Duplicate** | Delete. |
| `docs/product/PRD.md` | **✅ Active** | Rewrite product requirements. |
| `docs/product/ROADMAP.md` | **✅ Active** | Relocate roadmap to `docs/release/ROADMAP.md`. |
| `docs/product/PRICING.md` | **🗄️ Archive** | Move to `docs/archive/` |
| `docs/product/PMF_EXECUTION_PLAN.md` | **🗄️ Archive** | Move to `docs/archive/` |
| `docs/product/PROJECT_CONTEXT.md` | **✅ Active** | Keep baseline project context. |

---

### `archive/` & `scripts/` Directories

| Document | Classification | Target Action |
|:---|:---:|:---|
| `archive/README.md` | **✅ Active** | Keep. |
| `archive/audit_2026_reports/*` | **🗄️ Archive** | Keep. |
| `archive/reports/*` | **🗄️ Archive** | Keep. |
| `scripts/README.md` | **✅ Active** | Keep. |
