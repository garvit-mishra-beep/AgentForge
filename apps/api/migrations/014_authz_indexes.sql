-- Migration 014: Indexes for ownership-filtered hot paths
-- tasks/executions are filtered by created_by on every list/analytics query
-- (TOP_FINDINGS #16/#17) but lacked covering indexes -> sequential scans at scale.

CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_executions_created_by ON executions(created_by);
