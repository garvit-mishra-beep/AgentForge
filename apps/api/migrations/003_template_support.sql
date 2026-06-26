-- AgentForge Template Support Migration
-- Adds tester role, test message type, and instructions column

ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'tester';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'test';

ALTER TABLE team_members ADD COLUMN IF NOT EXISTS instructions TEXT NOT NULL DEFAULT '';
