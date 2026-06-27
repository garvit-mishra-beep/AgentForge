-- Add missing values to agent_role and message_type DB enums in case they were not fully applied
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'planner';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'deployment';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'evidence_validator';

ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'evidence_validation';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'deployment';
