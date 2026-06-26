-- Migration 008: Analytics
-- Tracks granular events for analytics computation

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES executions(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_project ON analytics_events(project_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created ON analytics_events(created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user ON analytics_events(created_by);

-- Analytics snapshots for pre-computed aggregates
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id UUID PRIMARY KEY,
    snapshot_type VARCHAR(50) NOT NULL,
    snapshot_date DATE NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(snapshot_type, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_type_date ON analytics_snapshots(snapshot_type, snapshot_date);
