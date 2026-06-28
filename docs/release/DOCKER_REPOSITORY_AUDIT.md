# Docker Repository Audit Report

## Findings

### 1. Missing pydantic-settings dependency in apps/api/pyproject.toml
- **Severity**: High
- **File**: apps/api/pyproject.toml
- **Root cause**: The `pydantic-settings>=2.1.0,<3.0.0` package is missing from the `dependencies` list, but the application imports `pydantic_settings` in `apps/api/core/config.py`.
- **Exact fix**: Add `"pydantic-settings>=2.1.0,<3.0.0",` to the `dependencies` array in `apps/api/pyproject.toml` (after the `pydantic` line).
- **Classification**: BROKEN (causes `ModuleNotFoundError` when installing via `pip install .`)

### 2. Version conflict for uvicorn[standard] between requirements.txt and pyproject.toml
- **Severity**: Medium
- **Files**: 
  - apps/api/requirements.txt (specifies `uvicorn[standard]==0.24.0`)
  - apps/api/pyproject.toml (requires `uvicorn[standard]>=0.27.0,<0.28.0`)
- **Root cause**: The version of uvicorn specified in requirements.txt does not satisfy the version constraint in pyproject.toml, leading to inconsistent installations between development (using requirements.txt) and Docker (using pyproject.toml via editable install).
- **Exact fix**: Align the versions. Since the Docker build uses pyproject.toml, update apps/api/requirements.txt to use `uvicorn[standard]>=0.27.0,<0.28.0` to match.
- **Classification**: BROKEN (causes version mismatch and potential installation conflicts)

### 3. Insecure default for JWT secret in docker-compose.yml
- **Severity**: Medium
- **File**: docker-compose.yml
- **Root cause**: The environment variable `AGENTFORGE_JWT_SECRET` is set to a weak default value (`dev-jwt-secret-do-not-use-in-production-1234`) which is unsuitable for production.
- **Exact fix**: Remove the hardcoded value and rely on external configuration (e.g., .env file or environment variable) without providing a default. For example:
  ```yaml
  AGENTFORGE_JWT_SECRET: "${AGENTFORGE_JWT_SECRET}"
  ```
  Update the accompanying documentation (e.g., .env.example) to clearly state that this variable must be set to a strong secret in production.
- **Classification**: RISKY (exposes weak secret if used in production)

### 4. Missing encryption key in docker-compose.yml
- **Severity**: Medium
- **File**: docker-compose.yml
- **Root cause**: The environment variable `AGENTFORGE_ENCRYPTION_KEY` is not set in the docker-compose.yml file, leaving it empty unless provided via an external .env file or environment. The application logs a warning but does not fail, potentially leading to unencrypted storage of sensitive data if the user expects encryption to be enabled by default.
- **Exact fix**: Similar to the JWT secret, do not hardcode a value. Instead, rely on external configuration:
  ```yaml
  AGENTFORGE_ENCRYPTION_KEY: "${AGENTFORGE_ENCRYPTION_KEY}"
  ```
  Update documentation to instruct users to set this to a 32-byte base64-encoded key in production.
- **Classification**: RISKY (risk of unencrypted sensitive data if key not provided)

### 5. Hardcoded environment values in docker-compose.yml override .env file
- **Severity**: Low
- **File**: docker-compose.yml
- **Root cause**: The `environment` section in the `api` service sets explicit values for variables like `AGENTFORGE_DATABASE_URL` and `AGENTFORGE_REDIS_URL`. These values override any values of the same name provided in an .env file or the environment, reducing flexibility.
- **Exact fix**: Change the assignment to use variable expansion with a default, allowing external configuration to override. For example:
  ```yaml
  AGENTFORGE_DATABASE_URL: "${AGENTFORGE_DATABASE_URL:-postgresql://agentforge:agentforge@postgres:5432/agentforge}"
  AGENTFORGE_REDIS_URL: "${AGENTFORGE_REDIS_URL:-redis://redis:6379/0}"
  ```
- **Classification**: VERIFIED (this is a configuration issue, not a broken build)

### 6. Root Dockerfile uses correct non-root user and healthcheck
- **Severity**: VERIFIED
- **File**: Dockerfile
- **Findings**: 
  - Uses multi-stage build.
  - Installs build dependencies (gcc) in the builder stage.
  - Creates a non-root user (`agentforge`) and switches to it.
  - Sets proper ownership and permissions.
  - Includes a HEALTHCHECK that checks the `/api/v1/health` endpoint.
  - Uses appropriate base images (python:3.11-slim).
- **Classification**: VERIFIED

### 7. apps/api/Dockerfile (unused) lacks security best practices
- **Severity**: Low
- **File**: apps/api/Dockerfile
- **Root cause**: This Dockerfile (not referenced in docker-compose.yml) runs as root, has no non-root user, and lacks a healthcheck.
- **Exact fix**: Although this file is not used in the main stack, for completeness and to avoid misuse, it should be updated to:
  - Add a non-root user and switch to it.
  - Add a healthcheck instruction.
  - Consider using .dockerignore to avoid copying unnecessary files.
  However, since it is not referenced in docker-compose.yml, this is a low-priority cleanup.
- **Classification**: NOT ENOUGH EVIDENCE (to deem it broken for the main workflow, but it is a code quality issue)

### 8. Dockerfile install command consistency with pyproject.toml
- **Severity**: VERIFIED
- **File**: Dockerfile
- **Finding**: The Dockerfile runs `pip install --no-cache-dir -e apps/api/` which installs the package in editable mode from the pyproject.toml. This is consistent with using pyproject.toml as the source of dependencies.
- **Classification**: VERIFIED

### 9. docker-compose.yml service definitions and dependencies
- **Severity**: VERIFIED
- **File**: docker-compose.yml
- **Findings**:
  - Defines three services: postgres, redis, api.
  - Uses appropriate images: postgres:16-alpine, redis:7-alpine.
  - Sets up healthchecks for both postgres (`pg_isready`) and redis (`redis-cli ping`).
  - Configures the api service to depend on both postgres and redis with `condition: service_healthy`.
  - Sets restart policy to `unless-stopped`.
  - Exposes ports: postgres (5432), redis (6379), api (8000).
  - Volumes: persists postgres data and mounts an initialization script.
- **Classification**: VERIFIED

### 10. Environment variables in docker-compose.yml for api service
- **Severity**: VERIFIED (with notes on the issues above)
- **File**: docker-compose.yml
- **Findings**: 
  - Sets `AGENTFORGE_DATABASE_URL` and `AGENTFORGE_REDIS_URL` to point to the respective services.
  - Sets other variables like `AGENTFORGE_AUTH_ENABLED`, `AGENTFORGE_JWT_SECRET`, `AGENTFORGE_LOG_LEVEL`, `AGENTFORGE_CORS_ORIGINS`.
  - Note: The hardcoded JWT secret and missing encryption key are issues (see above).
- **Classification**: VERIFIED (for the structure, but with specific findings on values)

### 11. PostgreSQL configuration in docker-compose.yml and initialization script
- **Severity**: VERIFIED
- **File**: docker-compose.yml and apps/api/migrations/001_initial.sql
- **Findings**:
  - Uses the official postgres:16-alpine image.
  - Sets environment variables for user, password, and database.
  - Mounts `./apps/api/migrations/001_initial.sql` to `/docker-entrypoint-initdb.d/001_initial.sql` for initialization.
  - The initialization script creates the pgcrypto extension, tables, and inserts a default user.
- **Classification**: VERIFIED

### 12. Redis configuration in docker-compose.yml
- **Severity**: VERIFIED
- **File**: docker-compose.yml
- **Findings**:
  - Uses the official redis:7-alpine image.
  - Exposes port 6379.
  - Sets a healthcheck using `redis-cli ping`.
- **Classification**: VERIFIED

### 13. Networking configuration in docker-compose.yml
- **Severity**: VERIFIED
- **File**: docker-compose.yml
- **Findings**:
  - Uses the default bridge network (no explicit network defined, which is fine for simple compose).
  - Services communicate via service names (postgres, redis) as hostnames.
- **Classification**: VERIFIED

### 14. Startup ordering in docker-compose.yml
- **Severity**: VERIFIED
- **File**: docker-compose.yml
- **Findings**:
  - The `api` service uses `depends_on` with `condition: service_healthy` for both postgres and redis, ensuring it starts only after both are healthy.
- **Classification**: VERIFIED

### 15. Security posture: non-root user, secrets handling, exposed ports, permissions
- **Severity**: Mixed (see specific findings)
- **Files**: Dockerfile, docker-compose.yml
- **Findings**:
  - **Non-root user**: The root Dockerfile creates and uses a non-root user (`agentforge`). ✅
  - **Secrets handling**: 
    - JWT secret and encryption key are passed via environment variables (good practice), but defaults are problematic (see findings 3 and 4).
    - No secrets are hardcoded in the image (except the problematic defaults).
  - **Exposed ports**: 
    - postgres: 5432 (exposed)
    - redis: 6379 (exposed)
    - api: 8000 (exposed)
    - These are appropriate for local development; in production, you might change the exposed ports or use a reverse proxy.
  - **Permissions**: 
    - The Dockerfile sets correct ownership of copied files to the non-root user.
- **Classification**: 
  - Non-root user: VERIFIED
  - Secrets handling: RISKY (due to default values)
  - Exposed ports: VERIFIED (for development context)
  - Permissions: VERIFIED

### 16. Consistency between requirements.txt, pyproject.toml, and Dockerfile install commands
- **Severity**: Mixed (see findings 1 and 2)
- **Files**: apps/api/requirements.txt, apps/api/pyproject.toml, Dockerfile
- **Findings**:
  - The Dockerfile installs from pyproject.toml via `pip install -e apps/api/` (correct).
  - requirements.txt and pyproject.toml have inconsistencies:
    - Missing pydantic-settings in pyproject.toml (finding 1).
    - Uvicorn version mismatch (finding 2).
- **Classification**: BROKEN (for the inconsistencies)

### 17. Build failures: identified
- **Severity**: High
- **File**: apps/api/pyproject.toml
- **Root cause**: Missing pydantic-selling dependency.
- **Exact fix**: As in finding 1.
- **Classification**: BROKEN (will cause build failure when using `pip install .`)

### 18. Startup failures: potential
- **Severity**: Medium
- **File**: docker-compose.yml
- **Root cause**: If the JWT secret or encryption key is not provided, the application may log warnings or fail to function correctly (e.g., encryption key missing leads to unencrypted API keys).
- **Exact fix**: As in findings 3 and 4.
- **Classification**: RISKY (may start but with degraded security)

### 19. Dependency mismatches: identified
- **Severity**: Medium
- **Files**: apps/api/requirementns.txt, apps/api/pyproject.toml
- **Root cause**: As in findings 1 and 2.
- **Exact fix**: As in findings 1 and 2.
- **Classification**: BROKEN

### 20. Broken paths or missing files: none found in the scoped files
- **Severity**: VERIFIED
- **Files**: Dockerfile, apps/api/Dockerfile, docker-compose.yml, .env.example, README.md, deployment docs, CI/CD workflows
- **Findings**: All referenced files exist and paths are correct.
- **Classification**: VERIFIED

## Summary

The Docker-related configuration is largely correct, with the main issues being:
1. A critical missing dependency (pydantic-settings) in pyproject.toml that will cause the build to fail.
2. A version mismatch for uvicorn between requirements.txt and pyproject.toml.
3. Insecure default values for secrets in docker-compose.yml.

All other aspects (Dockerfile structure, service definitions, healthchecks, dependencies, networking, etc.) are properly implemented.

To produce a working Docker-based deployment, the two breaking issues must be fixed, and the risky defaults should be addressed for production use.