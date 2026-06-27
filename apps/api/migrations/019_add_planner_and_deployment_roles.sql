-- Add planner, deployment, and evidence_validator roles to the agent_role enum
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'planner';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'deployment';
ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'evidence_validator';

-- Add evidence_validation and deployment to the message_type enum
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'evidence_validation';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'deployment';
