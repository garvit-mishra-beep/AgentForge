-- Add analytics columns to executions table
ALTER TABLE executions ADD COLUMN IF NOT EXISTS duration_ms INTEGER DEFAULT 0;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);
ALTER TABLE executions ADD COLUMN IF NOT EXISTS model VARCHAR(100);

-- Add project_id to tasks table for context/memory integration
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

-- Add aggregator to message_type enum for parallel agent output
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'aggregator';
