# Changelog — AgentForge

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [v1.0.0-rc1] — Release Candidate 1

### Added
* **Fast Demo Mode (`AGENTFORGE_FAST_DEMO_MODE=true`):** Strict sub-60-second task completion execution mode with single-pass graphs (no retry/review loops), reduced context history, and short model timeouts.
* **PyJWT local JWT authentication:** Replaced third-party Clerk dependencies with local bcrypt password hashing, access/refresh tokens, and native middleware.
* **Tenant Isolation:** Enforced database queries and task access filtering scoped by active `user_id` context.
* **Reorganized Repository Structure:** Cleaned root workspace by archiving historical audits, establishing standard documentation root files, and aligning subfolder layouts.
* **Verification Script Relocations:** Relocated loose root verification python scripts (`quick_verify_sandbox.py`, `verify_github_implementation.py`, `verify_sandbox_implementation.py`) to the `/scripts` directory and updated their path environments.
* **Test Module Relocations:** Relocated loose root tests (`test_evidence_gate.py`, `test_github_enhanced.py`, `test_repository_intelligence.py`, `test_validation_system.py`) to `apps/api/tests/` to run as part of the backend test suite.

### Fixed
* **LLM Provider Resolution:** Fixed fallback configuration checks preventing KeyErrors when retrieving agent timeouts.
* **Shadowing variables:** Resolved variable shadowing in the code review routes.
* **Rate Limit Enforcement:** Restored missing token bucket rate checks on the code review submit endpoint.
* **Nesting triple quotes Syntax Error:** Corrected quote terminations in `test_repository_intelligence.py` by switching outer double-quotes to single-quotes, enabling clean python compilation.

---

## [v0.3.0] — Real-Time Streaming & Task History

**Released:** 2026-06-15

### Added
* WebSocket real-time agent execution streaming.
* Task history lists with filtering (by project, status, date).
* Output panel displaying file logs and validation results.

### Fixed
* Message ordering bugs during state graph step delivery.

---

## [v0.2.0] — LangGraph Agent Execution

**Released:** 2026-06-01

### Added
* LangGraph state graph coordination (Lead, Builder, Reviewer).
* System-wide validation checks.

---

## [v0.1.0] — Initial Scaffold

**Released:** 2026-05-20

### Added
* Base monorepo workspace configurations.
