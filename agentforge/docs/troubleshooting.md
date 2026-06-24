# Troubleshooting Guide

## Common Issues

### Database Connection

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Causes:**
- PostgreSQL container not running
- Wrong connection string in `.env`
- Port conflict (default: 5432)

**Solutions:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Verify connection string
echo $DATABASE_URL

# Check logs
docker compose logs postgres
```

### Redis Connection

**Error:** `Timeout connecting to server`

**Causes:**
- Redis container not running
- Wrong `REDIS_URL` in `.env`
- Firewall blocking port 6379

**Solutions:**
```bash
# Check if Redis is running
docker compose ps redis

# Ping Redis
docker compose exec redis redis-cli ping
# Expected: PONG
```

### Qdrant Connection

**Warning:** `Failed to obtain server version. Unable to check client-server compatibility.`

**Causes:**
- Qdrant container starting up
- Version mismatch between client and server
- Wrong `QDRANT_URL` in `.env`

**Solutions:**
```bash
# Check if Qdrant is running
docker compose ps qdrant

# Verify API
curl http://localhost:6333/collections
```

### JWT Issues

**Error:** `FATAL: JWT_SECRET is not set` (application exits)

**Solution:** Set `JWT_SECRET` in `.env` to a random value:
```bash
openssl rand -hex 32
```

**Error:** `Invalid or expired token`

**Solution:** Obtain a new token via `/api/v1/auth/token`.

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solutions:**
- Wait for the rate limit window to reset
- Reduce request frequency
- Check `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_PERIOD` settings

### LLM Provider Errors

**Error:** `401 Unauthorized` from LLM provider

**Solutions:**
- Check API key in `.env`
- Verify the API key has sufficient quota
- Check provider status page for outages

### WebSocket Issues

**Symptom:** WebSocket connection fails or drops

**Solutions:**
- Verify Redis is running (WebSocket pub/sub)
- Check `WEBSOCKET_HEARTBEAT_INTERVAL` setting
- Ensure client supports WebSocket protocol

## Health Check Diagnostics

```bash
# Liveness (process alive)
curl http://localhost:8000/api/v1/live

# Readiness (database connected)
curl http://localhost:8000/api/v1/ready

# Full health (all services)
curl http://localhost:8000/api/v1/health

# Prometheus metrics
curl http://localhost:8000/metrics
```

## Debug Mode

Set `LOG_LEVEL=DEBUG` and `ENVIRONMENT=development` in `.env`:
```env
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

This enables:
- SQLAlchemy query logging
- Detailed request/response logging
- Full traceback in error responses
- Swagger UI at `/docs`

## Getting Help

- Open a GitHub issue with:
  - Steps to reproduce
  - Environment details (OS, Python version, Docker version)
  - Relevant logs and error messages
  - `.env` contents (with secrets redacted)
