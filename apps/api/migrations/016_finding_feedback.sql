-- Migration 016: Finding feedback (quality flywheel)
-- Captures whether a developer accepted or rejected each review finding so the
-- critic can learn to suppress low-signal patterns over time
-- (FEATURE_GAP "continuously-learning critic", Major Bet #2).

CREATE TABLE IF NOT EXISTS finding_feedback (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id      UUID,
    fingerprint  VARCHAR(32) NOT NULL,
    title        TEXT NOT NULL,
    severity     VARCHAR(16) NOT NULL DEFAULT 'medium',
    decision     VARCHAR(16) NOT NULL CHECK (decision IN ('accepted', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_finding_feedback_user ON finding_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_finding_feedback_fingerprint ON finding_feedback(fingerprint);
CREATE INDEX IF NOT EXISTS idx_finding_feedback_user_project
    ON finding_feedback(user_id, project_id);
