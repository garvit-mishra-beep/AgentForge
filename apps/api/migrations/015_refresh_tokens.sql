-- Migration 015: Refresh token store (rotation + revocation)
-- Previously /refresh minted new tokens with no server-side state, so refresh
-- tokens could not be revoked and logout was impossible (TOP_FINDINGS #5).
-- We persist each refresh token's jti and revoke on rotation / logout.

CREATE TABLE IF NOT EXISTS refresh_tokens (
    jti          UUID PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN NOT NULL DEFAULT FALSE,
    replaced_by  UUID,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
