# Documentation Index

Single source of truth for the **state** of every document in AgentForge.

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Active | Authoritative — read this for current behavior |
| 🔄 Needs Update | Mostly correct but stale in places; PRs welcome |
| 🗄️ Deprecated | Kept for history only; link in the replacement doc |
| 📦 Archive | Belongs in `archive/`; do not cite as truth |

## Recommended Reading Order

1. [`README.md`](../README.md) — what AgentForge is
2. [`architecture/SYSTEM_ARCHITECTURE.md`](./architecture/SYSTEM_ARCHITECTURE.md) — how it works
3. [`development/ONBOARDING.md`](./development/ONBOARDING.md) — get it running
4. [`api/API.md`](./api/API.md) — public contract
5. [`security/SECURITY_MODEL.md`](./security/SECURITY_MODEL.md) — trust boundaries
6. [`product/ROADMAP.md`](./product/ROADMAP.md) — where it's going

---

## Architecture (`docs/architecture/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [SYSTEM_ARCHITECTURE.md](./architecture/SYSTEM_ARCHITECTURE.md) | Engineers | ✅ Active | 2026-06-26 |
| [TECH_SPEC.md](./architecture/TECH_SPEC.md) | Engineers | ✅ Active | 2026-06-26 |
| [SCHEMA.md](./architecture/SCHEMA.md) | Engineers | ✅ Active | 2026-06-26 |
| [AGENT_ROLES.md](./architecture/AGENT_ROLES.md) | Engineers + Product | ✅ Active | 2026-06-26 |
| [AGENT_PROMPTS.md](./architecture/AGENT_PROMPTS.md) | Engineers | ✅ Active | 2026-06-26 |
| [PROMPTS.md](./architecture/PROMPTS.md) | Engineers | ✅ Active | 2026-06-26 |
| [AGENT_MEMORY.md](./architecture/AGENT_MEMORY.md) | Engineers | ✅ Active | 2026-06-26 |
| [MODEL_REGISTRY.md](./architecture/MODEL_REGISTRY.md) | Engineers | 🔄 Needs Update | 2026-06-26 |
| [HALLUCINATION_GUARD.md](./architecture/HALLUCINATION_GUARD.md) | Engineers | ✅ Active | 2026-06-26 |

## API (`docs/api/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [API.md](./api/API.md) | Integrators + Eng | ✅ Active | 2026-06-26 |

## Development (`docs/development/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [ONBOARDING.md](./development/ONBOARDING.md) | New contributors | ✅ Active | 2026-06-26 |
| [SETUP.md](./development/SETUP.md) | New contributors | ✅ Active | 2026-06-26 |
| [TESTING.md](./development/TESTING.md) | Engineers | ✅ Active | 2026-06-26 |
| [CONVENTIONS.md](./development/CONVENTIONS.md) | Engineers | ✅ Active | 2026-06-26 |
| [DX.md](./development/DX.md) | Engineers | ✅ Active | 2026-06-26 |
| [ENV.md](./development/ENV.md) | Engineers + Ops | ✅ Active | 2026-06-26 |
| [PERFORMANCE.md](./development/PERFORMANCE.md) | Engineers | ✅ Active | 2026-06-26 |
| [OBSERVABILITY.md](./development/OBSERVABILITY.md) | Engineers + Ops | ✅ Active | 2026-06-26 |
| [DECISIONS.md](./development/DECISIONS.md) | Engineers | ✅ Active | 2026-06-26 |
| [FAQ.md](./development/FAQ.md) | Everyone | ✅ Active | 2026-06-26 |
| [GLOSSARY.md](./development/GLOSSARY.md) | Everyone | ✅ Active | 2026-06-26 |
| [CONTRIBUTING.md](./development/CONTRIBUTING.md) | Contributors | ✅ Active | 2026-06-26 |
| [CLAUDE.md](./development/CLAUDE.md) | Claude Code sessions | ✅ Active | 2026-06-26 |
| [AUDIT.md](./development/AUDIT.md) | Engineers | 🔄 Needs Update | 2026-06-26 |
| [BUGS.md](./development/BUGS.md) | Engineers | 🔄 Needs Update | 2026-06-26 |

## Deployment (`docs/deployment/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [DEPLOYMENT.md](./deployment/DEPLOYMENT.md) | Operators | ✅ Active | 2026-06-26 |

## Security (`docs/security/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [SECURITY_MODEL.md](./security/SECURITY_MODEL.md) | Engineers + Security | ✅ Active | 2026-06-26 |
| [SECURITY.md](./security/SECURITY.md) | Operators + Users | ✅ Active | 2026-06-26 |
| [INCIDENT_RUNBOOK.md](./security/INCIDENT_RUNBOOK.md) | On-call | ✅ Active | 2026-06-26 |
| [DATA_PRIVACY.md](./security/DATA_PRIVACY.md) | Legal + Users | ✅ Active | 2026-06-26 |

## Product (`docs/product/`)

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [PRD.md](./product/PRD.md) | Product | ✅ Active | 2026-06-26 |
| [ROADMAP.md](./product/ROADMAP.md) | Product + Eng | ✅ Active | 2026-06-26 |
| [PRICING.md](./product/PRICING.md) | GTM | ✅ Active | 2026-06-26 |
| [PMF_EXECUTION_PLAN.md](./product/PMF_EXECUTION_PLAN.md) | Founders | 🔄 Needs Update | 2026-06-26 |
| [PROJECT_CONTEXT.md](./product/PROJECT_CONTEXT.md) | Everyone | ✅ Active | 2026-06-26 |

## Root

| Document | Audience | Status | Last Reviewed |
|----------|----------|--------|---------------|
| [README.md](../README.md) | Everyone | ✅ Active | 2026-06-26 |
| [REPOSITORY_MAP.md](../REPOSITORY_MAP.md) | Everyone | ✅ Active | 2026-06-26 |
| [CHANGELOG.md](./CHANGELOG.md) | Everyone | ✅ Active | 2026-06-26 |
| [TERMS_OF_USE.md](./TERMS_OF_USE.md) | Users + Legal | ✅ Active | 2026-06-26 |

---

## How to Update This Index

When you add or materially change a doc:

1. Update its row above.
2. Bump the **Last Reviewed** date.
3. Move the row to a different status column if needed.
4. Cross-link from the most relevant parent README.