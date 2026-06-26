-- Add parallel agent roles to the agent_role enum
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'security';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'architect';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'aggregator';

-- Add analytics columns to executions table
ALTER TABLE executions ADD COLUMN IF NOT EXISTS duration_ms INTEGER DEFAULT 0;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);
ALTER TABLE executions ADD COLUMN IF NOT EXISTS model VARCHAR(100);
