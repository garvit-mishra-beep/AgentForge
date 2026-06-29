# Security Truth Report

`Version: 1.0` · `Audit Focus: Cryptographic Controls, Auth Policies & Sandboxing`

This report outlines the verified security controls implemented inside the AgentForge platform.

---

## 1. Cryptographic Implementations

### 1.1 BYOK Encryption at Rest
-   **Algorithm**: **AES-256-GCM** (authenticated encryption with associated data).
-   **Service File**: [encryption.py](file:///c:/Users/garvi/AgentForge/apps/api/core/encryption.py).
-   **Implementation**: Utilizes `cryptography.hazmat.primitives.ciphers.aead.AESGCM` with a 12-byte cryptographically secure random nonce (`os.urandom(12)`) prefixed to the ciphertext.
-   **Ephemerality**: If `AGENTFORGE_ENCRYPTION_KEY` is not provided in environment variables, the service dynamically initializes an ephemeral key. Ephemeral mode prints a warning warning that encrypted credentials will be unrecoverable on service reboot.

---

## 2. Authentication & Authorization Policies

### 2.1 JWT Signature Flow
-   **Signing Algorithm**: `HS256` (HMAC using SHA-256).
-   **Authentication Middleware**: [auth.py](file:///c:/Users/garvi/AgentForge/apps/api/app/auth.py).
-   **Token Expiration**: Access tokens default to `jwt_expire_minutes` (configured via backend settings) and refresh tokens expire in `jwt_refresh_expire_days`.
-   **Security Controls**: A separate `jwt_refresh_secret` is required for production authorization settings to prevent key reuse attacks.

### 2.2 IDOR Prevention & Tenant Isolation
-   Every secured endpoint resolves the caller's context via the FastAPI dependency `Depends(require_user)`.
-   SQL queries verify ownership filtering on user boundaries:
```sql
SELECT 1 FROM teams WHERE id = $1 AND created_by = $2
```
This blocks horizontal access to tasks, teams, projects, credentials, and configurations belonging to other tenants.

---

## 3. Runtime Sandbox Safety

### 3.1 Container Security Profile
Inside [sandbox_executor.py](file:///c:/Users/garvi/AgentForge/apps/api/app/services/sandbox_executor.py):
-   **Capabilities**: Drops all default Linux capabilities by default (`drop_all_capabilities = True`).
-   **Privileges**: Enforces `no_new_privileges = True` to block setuid/setgid binary escalation attacks.
-   **Syscall Filtering**: Restricts system calls using a custom seccomp profile (`SCMP_ACT_ERRNO` default action) allowing only standard file read/write operations, thread creation, and process exits.
-   **User Namespace**: Enforces non-root execution (`user_id = 1000`, `group_id = 1000`).
-   **Resource Caps**: CPU usage limited to 1.0 core, Memory capped at 512MB, execution timeouts capped at 30 seconds.

### 3.2 Subprocess Fallback Risk
If the host environment does not run Docker daemon or Docker SDK is not installed, code execution falls back to restricted host process runs. This fallback path presents a potential system security risk if untrusted code is executed outside a strict container jail.
