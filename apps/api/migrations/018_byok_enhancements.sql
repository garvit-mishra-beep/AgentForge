-- AgentForge BYOK Enhancement Migration
-- Enhances api_keys table and adds supporting tables for full BYOK support

-- Drop indexes if they exist (for safety, though IF NOT EXISTS in CREATE would handle this)
-- We'll alter the existing table instead of dropping and recreating

-- Add project_id column to api_keys table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_keys' AND column_name = 'project_id'
    ) THEN
        ALTER TABLE api_keys ADD COLUMN project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Update the unique constraint to include project_id
DO $$
BEGIN
    -- Drop old constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'api_keys' AND constraint_name = 'uq_user_provider'
    ) THEN
        ALTER TABLE api_keys DROP CONSTRAINT uq_user_provider;
    END IF;

    -- Add new constraint that includes project_id (allowing NULL project_id for user-level keys)
    ALTER TABLE api_keys ADD CONSTRAINT uq_user_project_provider
    UNIQUE (user_id, project_id, provider);
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add column for provider-specific configuration (for custom endpoints, etc.)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_keys' AND column_name = 'provider_config'
    ) THEN
        ALTER TABLE api_keys ADD COLUMN provider_config JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add column for tracking if this is a default key for the user/project
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_keys' AND column_name = 'is_default'
    ) THEN
        ALTER TABLE api_keys ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Create table for custom API endpoints (OpenAI-compatible)
CREATE TABLE IF NOT EXISTS api_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL,
    provider VARCHAR(20) NOT NULL DEFAULT 'openai-compatible',  -- openai-compatible, openrouter, groq, etc.
    name VARCHAR(100) NOT NULL,  -- Friendly name for the endpoint
    base_url TEXT NOT NULL,      -- Base URL for the API endpoint
    api_key_id UUID NULL REFERENCES api_keys(id) ON DELETE SET NULL,  -- Optional: if endpoint uses a key from api_keys
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    headers JSONB DEFAULT '{}'::jsonb,  -- Custom headers to send with requests
    config JSONB DEFAULT '{}'::jsonb,   -- Additional provider-specific configuration
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure unique combination for user/project/provider/name
    UNIQUE (user_id, project_id, provider, name)
);

CREATE INDEX IF NOT EXISTS idx_api_endpoints_user_id ON api_endpoints(user_id);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_project_id ON api_endpoints(project_id);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_provider ON api_endpoints(provider);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_default ON api_endpoints(is_default) WHERE is_default = true;

-- Create table for AI usage tracking and cost analytics
CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0.0,
    request_id UUID,  -- For tracing requests through the system
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Additional metadata
    task_id UUID NULL REFERENCES tasks(id) ON DELETE SET NULL,
    execution_id UUID NULL REFERENCES executions(id) ON DELETE SET NULL,
    agent_role VARCHAR(50),  -- team_lead, builder, reviewer, etc.
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_user_id ON ai_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_project_id ON ai_usage(project_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_provider ON ai_usage(provider);
CREATE INDEX IF NOT EXISTS idx_ai_usage_model ON ai_usage(model);
CREATE INDEX IF NOT EXISTS idx_ai_usage_timestamp ON ai_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_usage_task_id ON ai_usage(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_execution_id ON ai_usage(execution_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_agent_role ON ai_usage(agent_role);

-- Create view for usage analytics
CREATE OR REPLACE VIEW v_ai_usage_summary AS
SELECT
    u.id as user_id,
    u.email as user_email,
    COALESCE(p.name, 'NO_PROJECT') as project_name,
    au.provider,
    au.model,
    COUNT(*) as request_count,
    SUM(au.prompt_tokens) as total_prompt_tokens,
    SUM(au.completion_tokens) as total_completion_tokens,
    SUM(au.total_tokens) as total_tokens,
    SUM(au.cost_usd) as total_cost_usd,
    AVG(au.cost_usd) as avg_cost_per_request,
    MAX(au.timestamp) as last_used_at,
    MIN(au.timestamp) as first_used_at
FROM ai_usage au
JOIN users u ON au.user_id = u.id
LEFT JOIN projects p ON au.project_id = p.id
GROUP BY u.id, u.email, p.name, au.provider, au.model
ORDER BY u.id, au.provider, au.model;

-- Update existing api_keys records to have default values for new columns
UPDATE api_keys SET project_id = NULL WHERE project_id IS NULL;
UPDATE api_keys SET provider_config = '{}'::jsonb WHERE provider_config IS NULL;
UPDATE api_keys SET is_default = FALSE WHERE is_default IS NULL;