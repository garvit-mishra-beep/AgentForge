-- Migration 017: GitHub App integration
-- Tracks app installations and a log of PR review runs (FEATURE_GAP "GitHub App /
-- PR review bot").

CREATE TABLE IF NOT EXISTS github_installations (
    installation_id  BIGINT PRIMARY KEY,
    account_login    TEXT,
    account_type     TEXT,
    user_id          UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS github_review_runs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id  BIGINT,
    repo             TEXT NOT NULL,
    pr_number        INTEGER NOT NULL,
    head_sha         TEXT,
    files_reviewed   INTEGER NOT NULL DEFAULT 0,
    findings         INTEGER NOT NULL DEFAULT 0,
    blocking         INTEGER NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_review_runs_repo_pr
    ON github_review_runs(repo, pr_number);
