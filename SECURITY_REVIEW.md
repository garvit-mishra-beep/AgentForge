# Security Review — AgentForge

## Score: 4.5/10

---

## 1. Authentication — ❌ 0/10

**No authentication exists**. The API is fully open:
- Every route uses `user_id = "00000000-0000-0000-0000-000000000001"`
- No middleware checks identity
- No session management
- No API key authentication for the API itself

**Risk**: Anyone who reaches the API can create teams, tasks, delete data, and run agent pipelines.

---

## 2. Secrets Management — ⚠️ 5/10

### Findings:

**P1 — Ephemeral encryption key** (`core/encryption.py:20-24`):
When `AGENTFORGE_ENCRYPTION_KEY` is not set, an ephemeral key is generated and used for AES-GCM encryption. All encrypted API keys become unrecoverable after server restart. A warning is logged but this is easy to miss.

```
if raw:
    self.key = base64.b64decode(raw)
else:
    self.key = AESGCM.generate_key(bit_length=256)  # EPHEMERAL
    logger.warning("No AGENTFORGE_ENCRYPTION_KEY set...")
```

**P2 — DB password in default config** (`core/config.py:5`):
```python
database_url: str = "postgresql://agentforge:agentforge@localhost:5432/agentforge"
```
If `AGENTFORGE_DATABASE_URL` is not set in production, the default falls back to a hardcoded password. This is a foot-gun.

**P2 — Clear-text DB password in `.env`**:
The `.env` file contains the password in plaintext. While `.env` is in `.gitignore`, file system permissions on production could leak it.

**P2 — Docker Compose hardcoded credentials**:
```
POSTGRES_USER: agentforge
POSTGRES_PASSWORD: agentforge
```

### Recommendations:
1. Always require `AGENTFORGE_ENCRYPTION_KEY` in production — fail to start if not set
2. Remove the default password from config.py and raise if not configured
3. Use Docker secrets or env_file for production credentials
4. Add startup validation that checks all required secrets are present

---

## 3. SQL Injection — ✅ 8/10

All database queries use parameterized queries (`$1`, `$2`, etc.) via asyncpg. No string interpolation in SQL.

**Minor issue**: The `clean_tables` fixture in `conftest.py:38-40` uses f-string interpolation:
```python
await pool.execute(f"DELETE FROM {table}")
```
This is test-only code and uses a whitelist of table names, so it's not exploitable, but it's a bad pattern.

---

## 4. SSRF / Prompt Injection — ⚠️ 5/10

**Ollama provider** makes HTTP requests to `settings.ollama_base_url + "/api/chat"`. If an attacker can control the Ollama URL, they can trigger SSRF. The URL is configured via env var, not user input, so risk is limited to compromised infrastructure.

**Prompt injection via user code**: The Quick Review pipeline passes user-submitted code directly into LLM prompts via Jinja2 templates. The templates auto-escape HTML but not LLM injection. This is by design (we want models to analyze the code), but there's no guard against prompt injection in code (e.g., code that says "ignore previous instructions").

---

## 5. Provider API Key Storage — ✅ 7/10

- BYOK uses AES-256-GCM encryption (correct algorithm, 12-byte nonce)
- Keys are encrypted before storage
- Preview masking shows only last 4 chars (good UX)
- Provider key validation checks both format and live connectivity

**Concern**: The `EncryptionService` is a module-level singleton (`_encryption`). In multi-worker deployments, each worker has its own singleton. This is fine since the encryption is stateless (key from env var), but the singleton pattern is fragile.

---

## 6. Frontend Security — ⚠️ 3/10

- **No CSP headers**: `next.config.ts` is empty — no security headers configured
- **Hardcoded secrets in examples**: `QuickReviewTextarea.tsx:12` has `SECRET = "my-dev-secret"`. While it's demo/example code, a user copying it could miss the context.
- **No input sanitization**: The review textarea sends raw user code to the API. Input length is limited (50KB) but there's no content-type validation.
- **XSS**: The UI renders review results including AI-generated issue descriptions. If an attacker can control the LLM output, they could inject HTML/JS. Currently rendered as text, but no explicit XSS guard.

---

## 7. CORS — ✅ 10/10

```python
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, ...)
```
CORS origins are configurable via `AGENTFORGE_CORS_ORIGINS` env var. Default is `["http://localhost:3000"]`. Production deployment should restrict this.

---

## 8. Security Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Authentication | 0/10 | None |
| Authorization | 0/10 | None |
| Secrets management | 5/10 | Ephemeral key, hardcoded defaults |
| SQL injection | 8/10 | Parameterized queries |
| SSRF | 5/10 | Ollama URL from env |
| Encryption (at rest) | 7/10 | AES-256-GCM, ephemeral key risk |
| Input validation | 7/10 | Pydantic + length limits |
| CORS | 10/10 | Configurable, restricted default |
| Security headers | 0/10 | No CSP/HSTS |
| Frontend XSS | 5/10 | No explicit guard on rendered LLM output |
| **Overall** | **4.5/10** | |

---

## 9. Priority Fixes

1. **P0**: Add authentication middleware (JWT or session-based)
2. **P1**: Make `AGENTFORGE_ENCRYPTION_KEY` required in production
3. **P1**: Remove hardcoded DB password from config.py default
4. **P2**: Add security headers in next.config.ts
5. **P2**: Add `Content-Security-Policy` header
6. **P2**: Add XSS guard for rendered LLM output
7. **P3**: Replace secret examples with `"CHANGE-ME"` placeholders
