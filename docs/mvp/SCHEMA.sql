-- ============================================================
-- AgentForge MVP — Database Schema
-- PostgreSQL 16
-- Migration: 001_initial
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLE: users
-- Single-user MVP. Will be extended with Clerk auth later.
-- ============================================================
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default user for MVP (single-user mode)
INSERT INTO users (id, email, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'default@agentforge.dev', 'Default User');

-- ============================================================
-- TABLE: teams
-- A team is a collection of agent role assignments.
-- Each team has exactly one of each role (team_lead, builder, reviewer).
-- ============================================================
CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_by  UUID NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_created_by ON teams(created_by);

-- ============================================================
-- TABLE: team_members
-- Each row assigns a model to a role within a team.
-- A team must have exactly 3 members: team_lead, builder, reviewer.
-- ============================================================
CREATE TYPE agent_role AS ENUM ('team_lead', 'builder', 'reviewer');

CREATE TABLE team_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id     UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role        agent_role NOT NULL,
    model       VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One role per team
    CONSTRAINT uq_team_member_role UNIQUE (team_id, role)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);

-- ============================================================
-- TABLE: tasks
-- A task is a unit of work submitted to a team.
-- ============================================================
CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed');

CREATE TABLE tasks (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id       UUID NOT NULL REFERENCES teams(id),
    title         VARCHAR(500) NOT NULL,
    description   TEXT NOT NULL,
    status        task_status NOT NULL DEFAULT 'pending',
    created_by    UUID NOT NULL REFERENCES users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_tasks_team ON tasks(team_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- ============================================================
-- TABLE: task_messages
-- Every agent output during execution is stored as a message.
-- Messages are ordered by step_order and created_at.
-- ============================================================
CREATE TYPE message_type AS ENUM ('plan', 'code', 'review', 'delivery', 'error', 'info');

CREATE TABLE task_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id       UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_order    INTEGER NOT NULL,
    role          agent_role NOT NULL,
    model         VARCHAR(100) NOT NULL,
    message_type  message_type NOT NULL,
    content       TEXT NOT NULL,
    metadata      JSONB DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Validate step_order is 1-based
    CONSTRAINT chk_step_order CHECK (step_order > 0)
);

CREATE INDEX idx_task_messages_task ON task_messages(task_id);
CREATE INDEX idx_task_messages_step ON task_messages(task_id, step_order);

-- ============================================================
-- TABLE: executions
-- Tracks the state of each task's graph execution.
-- graph_state is the serialized LangGraph state after each step.
-- ============================================================
CREATE TYPE execution_status AS ENUM ('running', 'completed', 'failed');

CREATE TABLE executions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id       UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status        execution_status NOT NULL DEFAULT 'running',
    graph_state   JSONB,
    current_node  VARCHAR(100),
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ,
    error_message TEXT,

    -- One execution per task
    CONSTRAINT uq_execution_task UNIQUE (task_id)
);

CREATE INDEX idx_executions_status ON executions(status);

-- ============================================================
-- Views
-- ============================================================

-- Active tasks with team info
CREATE VIEW v_active_tasks AS
SELECT
    t.id AS task_id,
    t.title,
    t.description,
    t.status,
    tm.name AS team_name,
    t.created_at,
    t.updated_at
FROM tasks t
JOIN teams tm ON tm.id = t.team_id
WHERE t.status IN ('pending', 'running')
ORDER BY t.created_at DESC;

-- Team composition (denormalized for fast reads)
CREATE VIEW v_team_composition AS
SELECT
    tm.id AS team_id,
    tm.name AS team_name,
    jsonb_object_agg(
        tmm.role::text,
        jsonb_build_object(
            'member_id', tmm.id,
            'model', tmm.model
        )
    ) AS members
FROM teams tm
LEFT JOIN team_members tmm ON tmm.team_id = tm.id
GROUP BY tm.id, tm.name;
