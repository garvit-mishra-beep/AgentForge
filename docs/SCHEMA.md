# Database Schema — AgentForge

**Version:** 1.0 | **Last Updated:** June 2026

---

## Entity-Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐
│    users     │       │    projects      │
│──────────────│       │──────────────────│
│ id (UUID)    │──┐    │ id (UUID)        │
│ clerk_id (T) │  │    │ name (T)         │
│ email (T)    │  │    │ description (T)  │
│ name (T)     │  │    │ owner_id (UUID)  │──┐
│ avatar_url(T)│  │    │ created_at (TS)  │  │
│ created_at   │  │    │ updated_at (TS)  │  │
│ updated_at   │  │    └────────┬─────────┘  │
└──────────────┘  │             │            │
                  │             │            │
                  │    ┌────────┴─────────┐  │
                  │    │  project_members │  │
                  │    │──────────────────│  │
                  │    │ id (UUID)        │  │
                  │    │ project_id (UUID)│──┘
                  └────│ user_id (UUID)   │──┘
                       │ role (ENUM)      │
                       │ joined_at (TS)   │
                       └──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│     teams        │       │     agents       │
│──────────────────│       │──────────────────│
│ id (UUID)        │       │ id (UUID)        │
│ project_id (UUID)│──┐    │ team_id (UUID)   │──┐
│ name (T)         │  │    │ role (ENUM)      │  │
│ created_at (TS)  │  │    │ model (T)        │  │
│ updated_at (TS)  │  │    │ system_prompt (T)│  │
└──────────────────┘  │    │ is_active (B)    │  │
                      │    │ created_at (TS)  │  │
                      │    └──────────────────┘  │
                      │                          │
┌──────────────────┐  │                          │
│     tasks        │  │                          │
│──────────────────│  │                          │
│ id (UUID)        │  │                          │
│ project_id (UUID)│──┘                          │
│ team_id (UUID)   │────┘                       │
│ title (T)        │                            │
│ description (T)  │                            │
│ status (ENUM)    │                            │
│ created_by (UUID)│──┘                         │
│ created_at (TS)  │                            │
│ updated_at (TS)  │                            │
│ completed_at (TS)│                            │
│ total_tokens (I) │                            │
│ total_cost (F)   │                            │
└───────┬──────────┘                            │
        │                                       │
        │  ┌──────────────────┐                 │
        │  │   task_steps     │                 │
        │  │──────────────────│                 │
        ├──│ task_id (UUID)   │                 │
        │  │ id (UUID)        │                 │
        │  │ agent_id (UUID)  │─────────────────┘
        │  │ step_order (I)   │
        │  │ status (ENUM)    │
        │  │ input (JSONB)    │
        │  │ output (JSONB)   │
        │  │ model (T)        │
        │  │ tokens_in (I)    │
        │  │ tokens_out (I)   │
        │  │ cost (F)         │
        │  │ confidence (F)   │
        │  │ started_at (TS)  │
        │  │ completed_at (TS)│
        │  └──────────────────┘
        │
        │  ┌──────────────────┐
        │  │    messages      │
        │  │──────────────────│
        ├──│ task_id (UUID)   │
        │  │ id (UUID)        │
        │  │ step_id (UUID)   │
        │  │ agent_id (UUID)  │
        │  │ role (T)         │
        │  │ content (TEXT)   │
        │  │ message_type (E) │
        │  │ created_at (TS)  │
        │  └──────────────────┘
        │
        │  ┌──────────────────┐
        │  │     outputs      │
        │  │──────────────────│
        ├──│ task_id (UUID)   │
        │  │ id (UUID)        │
        │  │ step_id (UUID)   │
        │  │ agent_id (UUID)  │
        │  │ file_path (T)    │
        │  │ file_content (T) │
        │  │ language (T)     │
        │  │ created_at (TS)  │
        │  └──────────────────┘

┌──────────────────────────┐
│    agent_memories        │
│──────────────────────────│
│ id (UUID)                │
│ agent_id (UUID)          │
│ task_id (UUID)           │
│ project_id (UUID)        │
│ role (T)                 │
│ content (TEXT)           │
│ embedding (VECTOR(1536)) │
│ metadata (JSONB)         │
│ created_at (TS)          │
│                          │
│ INDEX: ivfflat on        │
│   embedding (cosine)     │
│ INDEX: btree on          │
│   (project_id, role)     │
└──────────────────────────┘
```

---

## Table Definitions

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | Internal user ID |
| `clerk_id` | `VARCHAR(255)` | UNIQUE, NOT NULL | Clerk user ID |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL | User email |
| `name` | `VARCHAR(255)` | NOT NULL | Display name |
| `avatar_url` | `TEXT` | NULL | Profile image URL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

### projects

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `name` | `VARCHAR(255)` | NOT NULL | Project name |
| `description` | `TEXT` | NULL | Project description |
| `owner_id` | `UUID` | FK → users(id), NOT NULL | Project owner |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_projects_owner` on `owner_id`

### project_members

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `project_id` | `UUID` | FK → projects(id) ON DELETE CASCADE | |
| `user_id` | `UUID` | FK → users(id) ON DELETE CASCADE | |
| `role` | `VARCHAR(50)` | NOT NULL, CHECK IN ('owner','admin','member') | Access level |
| `joined_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_project_members_project` on `project_id`
Index: `idx_project_members_user` on `user_id`
Unique: `uq_project_member` on `(project_id, user_id)`

### teams

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `project_id` | `UUID` | FK → projects(id) ON DELETE CASCADE | Parent project |
| `name` | `VARCHAR(255)` | NOT NULL | Team name |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_teams_project` on `project_id`

### agents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `team_id` | `UUID` | FK → teams(id) ON DELETE CASCADE | Parent team |
| `role` | `VARCHAR(50)` | NOT NULL, CHECK IN ('team_lead','backend','frontend','qa','security','devops') | Agent role |
| `model` | `VARCHAR(100)` | NOT NULL | Assigned model ID from registry |
| `system_prompt` | `TEXT` | NULL | Override default system prompt |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Soft delete |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_agents_team` on `team_id`
Unique: `uq_agent_role_per_team` on `(team_id, role)`

### tasks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `project_id` | `UUID` | FK → projects(id) ON DELETE CASCADE | |
| `team_id` | `UUID` | FK → teams(id) ON DELETE SET NULL | Team assigned |
| `title` | `VARCHAR(500)` | NOT NULL | Short task title |
| `description` | `TEXT` | NOT NULL | Full task description |
| `status` | `VARCHAR(50)` | NOT NULL, DEFAULT 'pending', CHECK IN ('pending','running','awaiting_review','completed','failed','cancelled') | |
| `created_by` | `UUID` | FK → users(id), NOT NULL | Who created the task |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |
| `completed_at` | `TIMESTAMPTZ` | NULL | |
| `total_tokens` | `INTEGER` | NOT NULL, DEFAULT 0 | Cumulative token count |
| `total_cost` | `DECIMAL(12,6)` | NOT NULL, DEFAULT 0 | Cumulative USD cost |

Index: `idx_tasks_project_status` on `(project_id, status)`
Index: `idx_tasks_created_by` on `created_by`
Index: `idx_tasks_created_at` on `created_at`

### task_steps

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `task_id` | `UUID` | FK → tasks(id) ON DELETE CASCADE | |
| `agent_id` | `UUID` | FK → agents(id) ON DELETE SET NULL | |
| `step_order` | `INTEGER` | NOT NULL | Execution order (1-based) |
| `status` | `VARCHAR(50)` | NOT NULL, DEFAULT 'pending', CHECK IN ('pending','running','awaiting_review','completed','failed','skipped') | |
| `input` | `JSONB` | NULL | Input passed to the agent |
| `output` | `JSONB` | NULL | Agent output (structured) |
| `model` | `VARCHAR(100)` | NOT NULL | Model used for this step |
| `tokens_in` | `INTEGER` | NOT NULL, DEFAULT 0 | |
| `tokens_out` | `INTEGER` | NOT NULL, DEFAULT 0 | |
| `cost` | `DECIMAL(10,6)` | NOT NULL, DEFAULT 0 | |
| `confidence` | `DECIMAL(3,2)` | NULL | Agent self-reported confidence (0-1) |
| `started_at` | `TIMESTAMPTZ` | NULL | |
| `completed_at` | `TIMESTAMPTZ` | NULL | |

Index: `idx_task_steps_task` on `task_id`
Index: `idx_task_steps_agent` on `agent_id`

### messages

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `task_id` | `UUID` | FK → tasks(id) ON DELETE CASCADE | |
| `step_id` | `UUID` | FK → task_steps(id) ON DELETE CASCADE | |
| `agent_id` | `UUID` | FK → agents(id) ON DELETE SET NULL | |
| `role` | `VARCHAR(50)` | NOT NULL | Agent role label |
| `content` | `TEXT` | NOT NULL | Message text |
| `message_type` | `VARCHAR(50)` | NOT NULL, CHECK IN ('plan','code','review','test','security','summary','error','info') | |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_messages_task` on `task_id`
Index: `idx_messages_step` on `step_id`

### outputs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `task_id` | `UUID` | FK → tasks(id) ON DELETE CASCADE | |
| `step_id` | `UUID` | FK → task_steps(id) ON DELETE CASCADE | |
| `agent_id` | `UUID` | FK → agents(id) ON DELETE SET NULL | |
| `file_path` | `VARCHAR(1000)` | NOT NULL | Relative file path |
| `file_content` | `TEXT` | NOT NULL | Full file content |
| `language` | `VARCHAR(50)` | NULL | Detected language |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_outputs_task` on `task_id`

### agent_memories

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | |
| `agent_id` | `UUID` | FK → agents(id) ON DELETE CASCADE | |
| `task_id` | `UUID` | FK → tasks(id) ON DELETE CASCADE | |
| `project_id` | `UUID` | FK → projects(id) ON DELETE CASCADE | |
| `role` | `VARCHAR(50)` | NOT NULL | |
| `content` | `TEXT` | NOT NULL | Memory text |
| `embedding` | `VECTOR(1536)` | NOT NULL | OpenAI text-embedding-3-small |
| `metadata` | `JSONB` | NULL, DEFAULT '{}' | Arbitrary metadata |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT NOW() | |

Index: `idx_memories_project_role` on `(project_id, role)`
Index: `idx_memories_agent` on `agent_id`
Index: `idx_memories_embedding` — IVFFLAT with cosine distance on `embedding`
