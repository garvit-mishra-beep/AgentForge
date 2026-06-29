# Route Discovery Report

All 78 active endpoints across 13 routers. File:line citations confirmed for every route.

---

## Auth Routes — `app/routes/auth.py` (8 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/auth/login | Open | LoginRequest | AuthResponse | 50-89 |
| POST | /api/v1/auth/register | Open | RegisterRequest | AuthResponse | 92-121 |
| POST | /api/v1/auth/refresh | Open | RefreshRequest | RefreshResponse | 124-149 |
| POST | /api/v1/auth/logout | ✅ Bearer | LogoutRequest | 204 No Content | 152-159 |
| POST | /api/v1/auth/logout-all | ✅ Bearer | none | 204 No Content | 162-167 |

## Health Routes — `app/routes/health.py` (1 endpoint)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/health | Open | none | {status, version, timestamp, auth_enabled, fast_demo_mode, metrics} | 11-20 |

## Teams Routes — `app/routes/teams.py` (8 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/teams/template | ✅ Bearer | TeamTemplateCreate | TeamResponse | 22-54 |
| POST | /api/v1/teams | ✅ Bearer | TeamCreate | TeamResponse | 57-69 |
| GET | /api/v1/teams | ✅ Bearer | query: limit, offset | list[TeamResponse] | 72-103 |
| GET | /api/v1/teams/{team_id} | ✅ Bearer | none | TeamResponse | 106-116 |
| PUT | /api/v1/teams/{team_id} | ✅ Bearer | TeamCreate | TeamResponse | 119-138 |
| DELETE | /api/v1/teams/{team_id} | ✅ Bearer | none | 204 No Content | 141-153 |
| POST | /api/v1/teams/{team_id}/members | ✅ Bearer | TeamMemberCreate | TeamMemberResponse | 156-195 |
| PUT | /api/v1/teams/{team_id}/members/{member_id} | ✅ Bearer | TeamMemberUpdate | TeamMemberResponse | 198-228 |
| DELETE | /api/v1/teams/{team_id}/members/{member_id} | ✅ Bearer | none | 204 No Content | 231-244 |

## Tasks Routes — `app/routes/tasks.py` (4 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/tasks | ✅ Bearer | TaskCreate | TaskResponse | 46-93 |
| GET | /api/v1/tasks | ✅ Bearer | query: limit, offset | list[TaskResponse] | 96-126 |
| GET | /api/v1/tasks/{task_id} | ✅ Bearer | none | TaskResponse | 129-139 |
| GET | /api/v1/tasks/{task_id}/messages | ✅ Bearer | none | list[TaskMessageResponse] | 142-171 |

## Executions Routes — `app/routes/executions.py` (3 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/executions/detail/{exec_id} | ✅ Bearer | none | ExecutionResponse | 13-38 |
| GET | /api/v1/executions/{task_id} | ✅ Bearer | none | ExecutionResponse | 41-69 |
| GET | /api/v1/executions | ✅ Bearer | query: limit, offset | list[ExecutionResponse] | 72-100 |

## API Keys Routes — `app/routes/keys.py` (13 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/keys/providers | Open | none | ProviderInfoResponse | 95-97 |
| POST | /api/v1/keys/validate | Open | ApiKeyValidateRequest | ApiKeyValidateResponse | 100-123 |
| POST | /api/v1/keys | ✅ Bearer | ApiKeyCreate | ApiKeyResponse | 126-188 |
| GET | /api/v1/keys | ✅ Bearer | query: project_id, include_disabled | list[ApiKeyResponse] | 191-219 |
| GET | /api/v1/keys/{key_id} | ✅ Bearer | none | ApiKeyResponse | 222-239 |
| PUT | /api/v1/keys/{key_id} | ✅ Bearer | ApiKeyUpdate | ApiKeyResponse | 242-320 |
| DELETE | /api/v1/keys/{key_id} | ✅ Bearer | none | 204 No Content | 323-335 |
| POST | /api/v1/keys/{key_id}/set-default | ✅ Bearer | none | ApiKeyResponse | 338-381 |
| POST | /api/v1/keys/endpoints | ✅ Bearer | ApiEndpointCreate | ApiEndpointResponse | 385-448 |
| GET | /api/v1/keys/endpoints | ✅ Bearer | query: project_id, provider | list[ApiEndpointResponse] | 451-484 |
| GET | /api/v1/keys/endpoints/{endpoint_id} | ✅ Bearer | none | ApiEndpointResponse | 487-505 |
| PUT | /api/v1/keys/endpoints/{endpoint_id} | ✅ Bearer | ApiEndpointUpdate | ApiEndpointResponse | 508-620 |
| DELETE | /api/v1/keys/endpoints/{endpoint_id} | ✅ Bearer | none | 204 No Content | 623-635 |
| GET | /api/v1/keys/usage | ✅ Bearer | query: project_id, days | UsageStatsResponse | 638-732 |

## Review Routes — `app/routes/review.py` (4 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/review | Fallback demo | ReviewRequest | ReviewResponse | 235-284 |
| GET | /api/v1/review/{review_id} | Fallback demo | none | ReviewResult | 362-421 |
| GET | /api/v1/review/{review_id}/status | Fallback demo | none | {status} | 479-507 |
| GET | /api/v1/review/language/detect | Fallback demo | query: code | LanguageDetectionResponse | 424-475 |

## Projects Routes — `app/routes/projects.py` (12 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/projects | ✅ Bearer | ProjectCreate | ProjectResponse | 82-94 |
| GET | /api/v1/projects | ✅ Bearer | query: limit, offset | list[ProjectResponse] | 97-121 |
| GET | /api/v1/projects/{project_id} | ✅ Bearer | none | ProjectResponse | 124-134 |
| PUT | /api/v1/projects/{project_id} | ✅ Bearer | ProjectUpdate | ProjectResponse | 137-171 |
| DELETE | /api/v1/projects/{project_id} | ✅ Bearer | none | 204 No Content | 174-191 |
| POST | /api/v1/projects/{project_id}/teams | ✅ Bearer | ProjectTeamAssign | {status} | 197-227 |
| DELETE | /api/v1/projects/{project_id}/teams/{team_id} | ✅ Bearer | none | 204 No Content | 230-250 |
| POST | /api/v1/projects/{project_id}/upload | ✅ Bearer | multipart: file, parent_id | FileResponse | 256-317 |
| POST | /api/v1/projects/{project_id}/upload/zip | ✅ Bearer | multipart: file | {status, files_extracted, files} | 320-399 |
| GET | /api/v1/projects/{project_id}/files | ✅ Bearer | query: parent_id | list[FileResponse] | 402-440 |
| GET | /api/v1/projects/{project_id}/files/{file_id} | ✅ Bearer | none | FileResponse | 443-463 |
| DELETE | /api/v1/projects/{project_id}/files/{file_id} | ✅ Bearer | none | 204 No Content | 466-489 |
| GET | /api/v1/projects/{project_id}/files/{file_id}/download | ✅ Bearer | none | FileResponse (binary) | 492-522 |

## Context Routes — `app/routes/context.py` (9 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/projects/{project_id}/context/parse/{file_id} | ✅ Bearer | none | {status, context_id, language, symbols, imports, chunks} | 41-159 |
| POST | /api/v1/projects/{project_id}/context/parse-all | ✅ Bearer | none | {total, results} | 162-218 |
| GET | /api/v1/projects/{project_id}/context/summary | ✅ Bearer | none | list[context summary] | 224-262 |
| GET | /api/v1/projects/{project_id}/context/symbols | ✅ Bearer | query: file_id, symbol_type, search, limit | list[symbols] | 265-324 |
| GET | /api/v1/projects/{project_id}/context/imports | ✅ Bearer | query: file_id, limit | list[imports] | 327-375 |
| GET | /api/v1/projects/{project_id}/context/chunks | ✅ Bearer | query: file_id, chunk_type, search, limit | list[chunks] | 378-434 |
| GET | /api/v1/projects/{project_id}/context/file/{file_id} | ✅ Bearer | none | {context_id, language, symbols, imports, chunks} | 437-507 |
| DELETE | /api/v1/projects/{project_id}/context/file/{file_id} | ✅ Bearer | none | 204 No Content | 510-524 |

## Analytics Routes — `app/routes/analytics.py` (6 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/analytics/dashboard | ✅ Bearer | none | {projects, teams, tasks, executions, tokens, files, api_keys} | 166-172 |
| GET | /api/v1/analytics/trends | ✅ Bearer | query: days | {executions, tasks_created} | 175-182 |
| GET | /api/v1/analytics/models | ✅ Bearer | none | list[{model, total, completed, failed, avg_duration_ms, tokens}] | 185-191 |
| GET | /api/v1/analytics/teams | ✅ Bearer | none | list[{id, name, total_execs, completed, failed, avg_duration_ms, tokens}] | 194-200 |
| POST | /api/v1/analytics/track | ✅ Bearer | raw JSON body | {id, status} | 203-221 |
| GET | /api/v1/analytics/export | ✅ Bearer | none | {exported_at, dashboard, trends, models, teams} | 224-240 |

## Memories Routes — `app/routes/memories.py` (6 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/memories | ✅ Bearer | query: project_id, team_id, memory_type, key, search, tags, min_importance, limit, offset | list[memory] | 22-49 |
| GET | /api/v1/memories/relevant | ✅ Bearer | query: context, project_id, team_id, limit | list[memory] | 52-67 |
| GET | /api/v1/memories/{memory_id} | ✅ Bearer | none | memory | 70-80 |
| POST | /api/v1/memories | ✅ Bearer | raw JSON body | {id, status} | 83-103 |
| PUT | /api/v1/memories/{memory_id} | ✅ Bearer | raw JSON body | {status} | 106-122 |
| DELETE | /api/v1/memories/{memory_id} | ✅ Bearer | none | 204 No Content | 125-133 |

## Feedback Routes — `app/routes/feedback.py` (2 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| POST | /api/v1/feedback | ✅ Bearer | FeedbackCreate | {status, fingerprint} | 26-44 |
| GET | /api/v1/feedback/stats | ✅ Bearer | none | feedback stats | 47-50 |

## GitHub Routes — `app/routes/github.py` (2 endpoints)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/integrations/github/status | Open | none | {configured, app_id_set, enhanced_features} | 21-37 |
| POST | /api/v1/integrations/github/webhook | HMAC sig | raw JSON | {ok} | 40-94 |

## Metrics Route — `app/main.py` (1 endpoint)

| Method | Path | Auth | Request Schema | Response Schema | Lines |
|--------|------|------|----------------|-----------------|-------|
| GET | /api/v1/metrics | Open | none | Prometheus text format | 208-210 |

## Inactive Routes (NOT imported in main.py)

### GitHub Enhanced Routes — `app/routes/github_enhanced.py`

| Method | Path | Lines | Notes |
|--------|------|-------|-------|
| GET | /api/v1/integrations/github/enhanced/status | 27-49 | Router not imported in main.py |
| POST | /api/v1/integrations/github/enhanced/repository/sync | 52-88 | Router not imported |
| POST | /api/v1/integrations/github/enhanced/pull-request/{repository_full_name:path}/review | 129-174 | Router not imported |
| POST | /api/v1/integrations/github/enhanced/webhook | 228-313 | Router not imported |

---

## Summary

| Category | Active | Inactive | Total |
|----------|--------|----------|-------|
| Auth | 5 | 0 | 5 |
| Health | 1 | 0 | 1 |
| Teams | 9 | 0 | 9 |
| Tasks | 4 | 0 | 4 |
| Executions | 3 | 0 | 3 |
| API Keys | 14 | 0 | 14 |
| Review | 4 | 0 | 4 |
| Projects | 13 | 0 | 13 |
| Context | 9 | 0 | 9 |
| Analytics | 6 | 0 | 6 |
| Memories | 6 | 0 | 6 |
| Feedback | 2 | 0 | 2 |
| GitHub | 2 | 0 | 2 |
| GitHub Enhanced | 0 | 4 | 4 |
| Metrics | 1 | 0 | 1 |
| **Total** | **78** | **4** | **82** |

## Open Routes (no auth required)

| Route | Notes |
|-------|-------|
| GET /api/v1/health | Health check |
| POST /api/v1/auth/login | Login |
| POST /api/v1/auth/register | Register |
| POST /api/v1/auth/refresh | Token refresh |
| GET /api/v1/keys/providers | Provider list |
| POST /api/v1/keys/validate | Key format/live validation |
| POST /api/v1/integrations/github/webhook | HMAC-signed |
| GET /api/v1/integrations/github/status | Status check |
| GET /api/v1/docs | Swagger UI |
| GET /api/v1/openapi.json | OpenAPI spec |
| GET /api/v1/redoc | ReDoc |
| GET /api/v1/metrics | Prometheus |
| POST /api/v1/review | Fallback to DEMO_USER_ID |
| GET /api/v1/review/{review_id} | Fallback to DEMO_USER_ID |
| GET /api/v1/review/{review_id}/status | Fallback to DEMO_USER_ID |
| GET /api/v1/review/language/detect | No auth |
