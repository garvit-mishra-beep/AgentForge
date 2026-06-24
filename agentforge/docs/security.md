# Security

## Security Architecture

### Authentication
- **JWT-based**: Access tokens (HS256 signed) with 30-minute expiry
- **Refresh Tokens**: 7-day expiry for token renewal
- **API Keys**: SHA-256 hashed in database, with expiry support
- **Password Hashing**: bcrypt with random salt per password

### Authorization (Tenant Isolation)
All data access is scoped to `tenant_id`. Every service method includes tenant filtering:

```python
# Example from AgentService.get()
async def get(self, agent_id: uuid.UUID, tenant_id: uuid.UUID):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.tenant_id == tenant_id)
    return (await self.db.execute(stmt)).scalar_one_or_none()
```

### JWT Token Structure
```json
{
  "sub": "user-id",
  "tenant_id": "tenant-uuid",
  "exp": 1700000000,
  "iat": 1699996400,
  "iss": "agentforge-api",
  "aud": "agentforge-api",
  "jti": "unique-token-id",
  "type": "access"
}
```

### Token Validation
- Signature verification via HS256
- Audience and issuer validation
- Expiry check with 10s leeway
- Unique jti per token
- Empty/default secret rejection at startup

## Security Measures

### Rate Limiting
| Endpoint | Requests | Window |
|---|---|---|
| `POST /auth/token` | 100 | 60s |
| `POST /auth/register` | 10 | 3600s |
| `POST /rag/upload` | 20 | 60s |

### Safe Expression Evaluation
The `safe_eval()` function uses AST parsing to prevent arbitrary code execution:
- Only allows: comparisons, boolean ops, arithmetic, dict/list literals, subscript access
- Rejects: imports, function calls, attribute access on unknown objects, lambdas

### File Upload Security
- File type validation via MIME type checks
- Maximum upload size: 10 MB
- Allowed types: `application/pdf`, `text/plain`, `text/markdown`

### Secret Validation
On startup, the application validates:
- `JWT_SECRET` is non-empty
- `JWT_SECRET` is not the default value
- `JWT_SECRET` is not whitespace only

### Audit Logging
All POST, PUT, PATCH, DELETE operations on platform resources are logged:
- Actor identity (user or API key)
- Resource type and identifier
- Timestamp and IP address
- Action type and status

## Vulnerability Reporting

See [SECURITY.md](../SECURITY.md) for our responsible disclosure policy.

## Security Checklist

### Pre-Deployment
- [ ] `JWT_SECRET` is a strong random value (min 32 bytes)
- [ ] All LLM API keys are stored in secrets manager
- [ ] CORS origins restricted to known domains
- [ ] Database credentials use least-privilege principle
- [ ] TLS/SSL enabled for all services
- [ ] Rate limiting configured for production traffic
- [ ] Audit logging enabled and monitored
- [ ] Upload size limits configured

### Ongoing
- [ ] Dependencies regularly updated (Dependabot recommended)
- [ ] Access tokens rotated periodically
- [ ] API keys with suspicious activity revoked
- [ ] Audit logs reviewed for anomalies
