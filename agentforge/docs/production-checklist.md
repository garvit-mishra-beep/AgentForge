# Production Checklist

## Pre-Deployment

### Environment Configuration
- [ ] `JWT_SECRET` is a random 32+ byte value (generate: `openssl rand -hex 32`)
- [ ] `DATABASE_URL` uses production credentials (not default dev credentials)
- [ ] `REDIS_URL` configured with TLS if crossing networks
- [ ] `QDRANT_URL` points to production Qdrant instance
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=INFO` or `WARNING`
- [ ] `ENABLE_JSON_LOGS=true` for log aggregation

### Database
- [ ] Migrations applied: `alembic upgrade head`
- [ ] Connection pooling configured (default: `pool_size=20`, `max_overflow=10`)
- [ ] `AUTO_MIGRATE=false` (use Alembic for production migrations)
- [ ] Read replica configured for analytics queries (optional)
- [ ] Backup strategy in place

### Security
- [ ] CORS origins restricted: `CORS_ORIGINS=["https://your-domain.com"]`
- [ ] All LLM API keys stored in secrets manager (not plaintext `.env`)
- [ ] Upload size limits configured (`MAX_UPLOAD_SIZE`)
- [ ] Rate limiting enabled and tuned for traffic patterns
- [ ] Audit logging enabled and log storage configured
- [ ] TLS/SSL termination configured (reverse proxy)

### Docker/Deployment
- [ ] Docker images tagged with version (not `latest`)
- [ ] Health checks configured in orchestration
- [ ] Resource limits set (CPU, memory)
- [ ] Log driver configured (json-file, journald, or cloud logger)
- [ ] Restart policy: `unless-stopped` or `always`

## Staging Validation

### Tests
- [ ] `pytest` passes (all 130+ tests)
- [ ] `pytest --cov=apps/api` meets 80% threshold
- [ ] Integration tests pass against staging services

### Observability
- [ ] `/api/v1/health` returns healthy
- [ ] `/api/v1/ready` returns healthy
- [ ] `/metrics` endpoint accessible and contains expected metrics
- [ ] Logs are being collected and searchable
- [ ] Alerts configured and tested

### Performance
- [ ] API responds under 500ms p95 for common operations
- [ ] Database connection pool not exhausted under load
- [ ] Rate limiting prevents abuse without blocking legitimate traffic

## Post-Deployment

### Monitoring
- [ ] Error rate < 1% for first 24 hours
- [ ] Memory usage stable (no leaks)
- [ ] No unexpected restarts
- [ ] LLM provider costs within expected range

### Security Scan
- [ ] Dependencies scanned for vulnerabilities
- [ ] No secrets committed to repository
- [ ] No debug endpoints exposed (disable `/docs` in production by default)

## Incident Response Preparation
- [ ] Runbook accessible to on-call team
- [ ] Rollback procedure documented and tested
- [ ] Access to logs, metrics, and tracing dashboards
- [ ] Database backup verified
