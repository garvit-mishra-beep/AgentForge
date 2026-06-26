-- Migration 009: Long-Term Memory
-- Stores agent memories for cross-session context

CREATE TABLE IF NOT EXISTS agent_memories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    key VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL DEFAULT 'general',
    importance REAL NOT NULL DEFAULT 0.5,
    tags TEXT[] DEFAULT '{}',
    source VARCHAR(100) DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_user ON agent_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_project ON agent_memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_team ON agent_memories(team_id);
CREATE INDEX IF NOT EXISTS idx_memories_key ON agent_memories(key);
CREATE INDEX IF NOT EXISTS idx_memories_type ON agent_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON agent_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created ON agent_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON agent_memories USING gin(tags);
