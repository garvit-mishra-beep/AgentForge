# AgentForge V1.0.0 — Release Notes

**Release Date:** June 28, 2026
**Tag:** `v1.0.0`

---

## 🎉 Highlights

AgentForge V1.0.0 is the first production release of the multi-agent AI development platform. This release represents a stable, security-hardened, and fully documented system ready for public use.

---

## 🚀 What's New in V1.0.0

### 🔑 BYOK Architecture — Bring Your Own Key
Users supply their own LLM API credentials. No shared model access. No data sent to third parties.

- **Per-user and per-project key scoping** — keys resolve at runtime: user-key → project-key → system fallback
- **AES-256 Fernet encryption at rest** — keys never stored in plaintext
- **Live key validation** — provider API is pinged before any key is persisted
- **Multi-provider support** — OpenAI, Anthropic, Google Gemini, OpenRouter, Groq

### 🤖 Multi-Agent Workflow Engine
A LangGraph DAG coordinates a full AI engineering team end-to-end:

```
Team Lead (Plan) → Builder (Code) → Reviewer (Audit) → Team Lead (Deliver)
```

- **Fast Demo Mode** — Hard-capped timeouts and single-pass graph for sub-60s execution
- **Configurable per-node timeouts** — Lead: 20s, Builder: 30s, Reviewer: 15s, Deliver: 15s

### 🔗 GitHub Native Integration
- GitHub App installation on any repository
- Webhooks trigger automatic code reviews on every Pull Request
- Agent findings posted inline as GitHub PR review comments
- `X-Hub-Signature-256` HMAC validation on all inbound webhooks

### 🛡️ Evidence Validation Gate
- Each agent output is validated for confidence score (0.0–1.0), completeness, and correctness before proceeding
- Below-threshold outputs are rejected with structured failure diagnostics

### 🔒 Security Hardening
- **Local authentication** — PyJWT access tokens + bcrypt hashed passwords. No external auth service.
- **Refresh token rotation** — Old tokens invalidated on each use
- **Tenant isolation** — All database queries are scoped to the authenticated `user_id`
- **Secret leakage prevention** — Keys and passwords never appear in logs or exception traces

### 🌳 Tree-Sitter Repository Intelligence
- Live codebase symbol indexing using Tree-Sitter parsers
- Dependency graph and call-scope context injected into agent prompts
- Supports Python, TypeScript, Go, Rust, Java, and more

### 📊 Observability
- Prometheus-compatible metrics at `/api/v1/metrics`
- Structured JSON logging with correlation IDs on every request
- Health endpoint at `/api/v1/health` (used by Docker HEALTHCHECK)

---

## 📈 Quality Metrics

| Metric | Value |
|:---|:---|
| Test suite | **208 / 208 passing** |
| Mypy type errors | **0** |
| Ruff lint findings | **0** |
| Migration scripts | **21 SQL files, auto-applied** |
| Supported providers | **5 (OpenAI, Anthropic, Google, OpenRouter, Groq)** |

---

## 🏗️ Infrastructure

- **Backend:** FastAPI + asyncpg + LangGraph
- **Database:** PostgreSQL 16 + pgvector
- **Cache / Streaming:** Redis 7 (Pub/Sub for real-time WebSocket delivery)
- **Auth:** PyJWT + bcrypt
- **Frontend:** Next.js 15 App Router
- **CLI:** Python Click
- **Deployment:** Docker Compose (local) / Railway (production)

---

## ⚠️ Known Limitations

The following limitations are acknowledged for V1.0.0 and scheduled for future roadmap items:

| Limitation | Notes |
|:---|:---|
| No password reset / email verification flow | Manual database intervention required; planned for V1.1 |
| No multi-user collaboration / team sharing | All resources are per-user scoped; RBAC teams are on the roadmap |
| No enterprise SSO / SAML | Username/password + bcrypt is the only auth path |
| No dedicated audit log UI | Events are emitted to metrics and logs but have no browsable interface |
| Load tested at small scale only | Designed for individual and small-team use; horizontal scaling not validated |

---

## 📄 Release Verification Reports

All audit reports generated during the V1.0.0 release cycle are available in `docs/release/`:

- [Fresh Clone Audit](docs/release/FRESH_CLONE_AUDIT.md)
- [Deployment Verification](docs/release/DEPLOYMENT_VERIFICATION.md)
- [BYOK Verification](docs/release/BYOK_VERIFICATION.md)
- [Security Release Audit](docs/release/SECURITY_RELEASE_AUDIT.md)
- [Resilience Audit](docs/release/RESILIENCE_AUDIT.md)
- [V1 Release Decision](docs/release/V1_RELEASE_DECISION.md)

---

## 🏷️ Tagging This Release

```bash
git tag -a v1.0.0 -m "AgentForge V1.0.0 — First production release"
git push origin v1.0.0
```
