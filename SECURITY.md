# Security Guide — AgentForge

Specifications for authentication flows, role access controls, BYOK provider key encryption, rate limiting, and prompt injection defenses.

---

## 1. Authentication Flow

AgentForge uses a local, secure authentication system utilizing bcrypt for password hashing and standard PyJWT JSON Web Tokens (JWT) for session management.

```text
Browser                                       FastAPI Backend
   │                                                 │
   │  1. Submit Username/Password                    │
   ├────────────────────────────────────────────────►│ (Verifies bcrypt hash)
   │                                                 │
   │  2. Return JWT Access + Refresh Tokens          │
   │◄────────────────────────────────────────────────┤
   │                                                 │
   │  3. Subsequent Requests + Bearer JWT Header     │
   ├────────────────────────────────────────────────►│ (Middleware validates JWT)
   │                                                 │
```

### JWT Validation Middleware
The authorization middleware (`app/auth.py`) intercepts incoming HTTP calls:
1. Validates the signature using the configured `JWT_SECRET`.
2. Checks expiration times.
3. Decodes user, role, and tenant isolation variables.
4. Checks Redis cache validation status.

---

## 2. AI Provider Key (BYOK) Encryption

AgentForge dynamically maps keys at execution time from three layers (Project, User, Global).

### Encryption at Rest
All API keys are encrypted at rest using AES-256 Fernet symmetric cryptography:
* **Key Generation:** A secure encryption key (`ENCRYPTION_KEY`) is stored in backend environment variables.
* **Storage:** Keys are encrypted before being written to PostgreSQL database fields (`api_keys`).

### Key Lifecycle
1. **Decryption:** Decrypted in memory *only* during active task execution by the agent nodes.
2. **Post-Execution:** Reference values are deleted immediately after the network call completes to ensure keys are garbage collected.
3. **Logs:** Plaintext keys are never output to log trace dumps or returned in public API payloads.

---

## 3. Rate Limiting

Rate limiting is enforced at the API routing layer using a Redis token bucket store:
* Limits are configured per IP address and user account identifier.
* Defaults are set to prevent API denial-of-service bursts:
  ```python
  # Settings: settings.review_rate_limit / settings.review_rate_window
  ```
* Requests hitting the limit return `429 Too Many Requests`.

---

## 4. Prompt Injection & PII Redaction

### Input Sanitization
User-provided prompts and code inputs are sanitized to strip system-role overrides:
* **Role stripping:** Block text sequences like `ignore previous instructions` or `forget all prior instructions`.
* **PII Redaction:** Regular expression matching filters out sensitive elements (SSNs, credit cards, emails, phone numbers) before prompts are fed to LLM API clients.

---

## 5. Vulnerability Reporting

If you find a security bug in AgentForge, please do not open a public issue. Email: **security@agentforge.dev**
We target a 72-hour triage window and coordinate disclosures following patch releases.
