# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.x (pre-release) | ✅ |
| < 0.1 | ❌ |

## Reporting a Vulnerability

We take the security of AgentForge AI seriously. If you believe you've found a security vulnerability, please follow these steps:

### Private Disclosure

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to **security@agentforge.ai** (or use the private reporting mechanism once GitHub enables it for this repository).

### What to Include

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested fix (if any)

### Expected Timeline

| Step | Timeframe |
|---|---|
| Acknowledgment | 24 hours |
| Initial assessment | 72 hours |
| Fix development | 5-10 business days |
| Public disclosure | 30 days after fix |

## Security Architecture

### Authentication & Authorization

- **JWT Tokens**: Signed with HS256, validated for audience, issuer, and expiry. Tokens include unique jti to prevent replay.
- **API Keys**: SHA-256 hashed in storage, never stored in plaintext. Support expiry dates.
- **Multi-Tenancy**: All database queries include tenant_id filtering. No cross-tenant data access.
- **Password Storage**: bcrypt with per-password salt. No plaintext storage.

### Input Validation

- **Pydantic Schemas**: All API inputs validated at the boundary
- **Safe Evaluation**: AST-based expression evaluator prevents arbitrary code execution
- **File Uploads**: MIME type validation, size limits (10 MB default)
- **Rate Limiting**: Per-IP, per-endpoint limits prevent abuse

### Secrets Management

- **Startup Validation**: Application exits if JWT_SECRET is empty or default
- **Environment Isolation**: `.env` files excluded from version control
- **No Hardcoded Secrets**: All credentials from environment variables

### Data Protection

- **Audit Logging**: All CRUD operations logged with actor, action, timestamp
- **Input Sanitization**: User-provided content validated and sanitized
- **Error Handling**: No sensitive data leaked in error responses

## Responsible Disclosure

We follow coordinated disclosure:

1. Reporter submits vulnerability privately
2. We acknowledge within 24 hours
3. We develop and test a fix
4. We release the fix and notify reporter
5. We publish a security advisory 30 days after fix release

We commit to:
- Responding promptly to all reports
- Keeping reporters informed of progress
- Providing credit for valid reports (if desired)
- Coordinating public disclosure timing

## Bug Bounty

This project is in pre-release and does not currently offer a bug bounty program. We may introduce one in future releases.
