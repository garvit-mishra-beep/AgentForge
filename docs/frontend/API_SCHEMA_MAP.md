# API Schema Map

All schemas from `models/schemas.py` (lines 1-354) with field-level detail.

---

## Enums

### ProviderName — Line 8
```
openai | anthropic | google | openrouter | groq
```

### AgentRole — Line 16
```
team_lead | builder | reviewer | tester | security | architect | aggregator | planner | deployment | evidence_validator
```

### MessageType — Line 29
```
plan | code | review | test | delivery | error | info | aggregator | evidence_validation | deployment | research | documentation
```

### TaskStatus — Line 44
```
pending | running | completed | failed
```

### ExecStatus — Line 51
```
running | completed | failed
```

---

## Auth Schemas

### LoginRequest — Lines 59-61
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | str | ✅ | min_length=1, max_length=255 |
| password | str | ✅ | min_length=8, max_length=128 |

### RegisterRequest — Lines 64-67
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | str | ✅ | min_length=1, max_length=255 |
| password | str | ✅ | min_length=8, max_length=128 |
| name | str | ✅ | min_length=1, max_length=255 |

### AuthResponse — Lines 70-75
| Field | Type | Description |
|-------|------|-------------|
| token | str | JWT access token (8hr expiry) |
| refresh_token | str | JWT refresh token (7d expiry, single-use) |
| user_id | str | UUID |
| email | str | |
| name | str | |

### RefreshRequest — routes/auth.py:28-29
| Field | Type | Required |
|-------|------|----------|
| refresh_token | str | ✅ |

### RefreshResponse — routes/auth.py:32-34
| Field | Type |
|-------|------|
| token | str |
| refresh_token | str |

### LogoutRequest — routes/auth.py:37-38
| Field | Type | Required |
|-------|------|----------|
| refresh_token | str | ✅ |

---

## Teams Schemas

### TeamCreate — Lines 80-82
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | str | ✅ | max_length=255 |
| description | str \| None | ❌ | max_length=2000 |

### TeamResponse — Lines 85-92
| Field | Type |
|-------|------|
| id | UUID \| str |
| name | str |
| description | str \| None |
| created_by | UUID \| str |
| created_at | datetime |
| updated_at | datetime |
| members | list[TeamMemberResponse] |

### TeamMemberCreate — Lines 95-97
| Field | Type | Required |
|-------|------|----------|
| role | AgentRole | ✅ |
| model | str | ✅, max_length=100 |

### TeamTemplateMember — Lines 100-103
| Field | Type |
|-------|------|
| role | AgentRole |
| model | str, max_length=100 |
| instructions | str |

### TeamTemplateCreate — Lines 106-110
| Field | Type |
|-------|------|
| name | str, max_length=255 |
| description | str \| None, max_length=2000 |
| use_case | str |
| members | list[TeamTemplateMember] |

### TeamMemberUpdate — Lines 113-114
| Field | Type | Required |
|-------|------|----------|
| model | str | ✅, max_length=100 |

### TeamMemberResponse — Lines 117-123
| Field | Type |
|-------|------|
| id | UUID \| str |
| team_id | UUID \| str |
| role | AgentRole |
| model | str |
| instructions | str |
| created_at | datetime |

---

## Tasks Schemas

### TaskCreate — Lines 128-132
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| team_id | str | ✅ | UUID format |
| title | str | ✅ | max_length=500 |
| description | str | ✅ | max_length=10000 |
| project_id | str \| None | ❌ | UUID format |

### TaskResponse — Lines 135-146
| Field | Type |
|-------|------|
| id | UUID \| str |
| team_id | UUID \| str |
| title | str |
| description | str |
| status | TaskStatus |
| created_by | UUID \| str |
| created_at | datetime |
| updated_at | datetime |
| completed_at | datetime \| None |
| error_message | str \| None |
| project_id | UUID \| str \| None |

### TaskMessageResponse — Lines 149-157
| Field | Type | Notes |
|-------|------|-------|
| id | UUID \| str | |
| task_id | UUID \| str | |
| step_order | int | Ordered within task |
| role | AgentRole | |
| model | str | |
| message_type | MessageType | |
| content | str | |
| created_at | datetime | **No `tokens` field** |

### TaskDetailResponse — Lines 160-161
Extends TaskResponse with:
| Field | Type |
|-------|------|
| messages | list[TaskMessageResponse] |

---

## Executions Schemas

### ExecutionResponse — Lines 166-173
| Field | Type |
|-------|------|
| id | UUID \| str |
| task_id | UUID \| str |
| status | str (running/completed/failed) |
| current_node | str \| None |
| started_at | datetime |
| completed_at | datetime \| None |
| error_message | str \| None |

---

## API Keys Schemas

### ApiKeyCreate — Lines 178-185
| Field | Type | Required |
|-------|------|----------|
| provider | ProviderName | ✅ |
| key | str | ✅ (stripped) |

### ApiKeyUpdate — Lines 188-195
| Field | Type | Required |
|-------|------|----------|
| key | str \| None | ❌ (stripped) |
| is_enabled | bool \| None | ❌ |

### ApiKeyResponse — Lines 198-205
| Field | Type |
|-------|------|
| id | UUID \| str |
| provider | ProviderName |
| key_preview | str (masked) |
| is_enabled | bool |
| is_default | bool |
| created_at | datetime |
| updated_at | datetime |

### ApiKeyValidateRequest — Lines 208-215
| Field | Type | Required |
|-------|------|----------|
| provider | ProviderName | ✅ |
| key | str | ✅ (stripped) |

### ApiKeyValidateResponse — Lines 218-223
| Field | Type |
|-------|------|
| valid | bool |
| provider | ProviderName |
| message | str |
| format_valid | bool |
| live_valid | bool \| None |

### ProviderInfoResponse — Lines 226-227
| Field | Type |
|-------|------|
| providers | dict |

---

## Projects Schemas

### ProjectCreate — Lines 236-238
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | str | ✅ | max_length=255 |
| description | str \| None | ❌ | max_length=2000 |

### ProjectUpdate — Lines 241-243
| Field | Type |
|-------|------|
| name | str \| None, max_length=255 |
| description | str \| None, max_length=2000 |

### ProjectResponse — Lines 246-253
| Field | Type |
|-------|------|
| id | UUID \| str |
| name | str |
| description | str \| None |
| created_by | UUID \| str |
| created_at | datetime |
| updated_at | datetime |
| team_ids | list[UUID \| str] |

### ProjectTeamAssign — Line 256-257
| Field | Type | Required |
|-------|------|----------|
| team_id | str | ✅ |

---

## Files Schemas

### FileResponse — Lines 262-275
| Field | Type |
|-------|------|
| id | UUID \| str |
| project_id | UUID \| str |
| parent_id | UUID \| str \| None |
| filename | str |
| filepath | str |
| mime_type | str |
| size_bytes | int |
| is_directory | bool |
| file_hash | str \| None |
| status | str |
| created_by | UUID \| str |
| created_at | datetime |
| updated_at | datetime |

---

## API Endpoints Schemas

### ApiEndpointCreate — Lines 280-286
| Field | Type | Required |
|-------|------|----------|
| provider | ProviderName | ✅ |
| name | str | ✅, max_length=255 |
| base_url | str | ✅ |
| api_key_id | str \| None | ❌ |
| headers | dict \| None | ❌ |
| config | dict \| None | ❌ |

### ApiEndpointUpdate — Lines 289-295
| Field | Type |
|-------|------|
| name | str \| None, max_length=255 |
| base_url | str \| None |
| api_key_id | str \| None |
| is_default | bool \| None |
| headers | dict \| None |
| config | dict \| None |

### ApiEndpointResponse — Lines 298-310
| Field | Type |
|-------|------|
| id | UUID \| str |
| user_id | UUID \| str |
| project_id | UUID \| str \| None |
| provider | str |
| name | str |
| base_url | str |
| api_key_id | UUID \| str \| None |
| is_default | bool |
| headers | dict \| None |
| config | dict \| None |
| created_at | datetime |
| updated_at | datetime |

---

## Review Schemas

### ReviewRequest — Lines 328-330
| Field | Type | Required |
|-------|------|----------|
| code | str | ✅, min_length=1 |
| language | str \| None | ❌ |

### ReviewResponse — Lines 333-335
| Field | Type |
|-------|------|
| review_id | str |
| status | str |

### ReviewResult — Lines 338-349
| Field | Type |
|-------|------|
| review_id | str |
| status | str |
| baseline_issues | list[dict] \| None |
| builder_output | str \| None |
| review_issues | list[dict] \| None |
| summary | str \| None |
| model_used | str \| None |
| created_at | str \| None |
| completed_at | str \| None |
| error | str \| None |
| failed_at | str \| None |

### LanguageDetectionResponse — Lines 352-354
| Field | Type |
|-------|------|
| language | str |
| confidence | float |

---

## Feedback Schema

### FeedbackCreate — routes/feedback.py:17-23
| Field | Type | Required |
|-------|------|----------|
| title | str | ✅, max_length=500 |
| decision | str | ✅, pattern="^(accepted\|rejected)$" |
| severity | str | default="medium" |
| file | str \| None | ❌ |
| project_id | str \| None | ❌ |
| task_id | str \| None | ❌ |

---

## Usage Schemas

### UsageDataPoint — Lines 313-316
| Field | Type |
|-------|------|
| date | str |
| cost_usd | float |
| tokens | int |

### UsageStatsResponse — Lines 319-323
| Field | Type |
|-------|------|
| total_cost_usd | float |
| total_requests | int |
| by_provider_model | list[dict] |
| daily_data | list[UsageDataPoint] |
