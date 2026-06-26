-- Migration 005: Auth and Migration Tracking
-- Adds user authentication support and schema migration tracking

-- Users: add password_hash for auth
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(128) NOT NULL DEFAULT '';

-- Set default password for demo user ('changeme')
UPDATE users
SET password_hash = '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881'
WHERE id = '00000000-0000-0000-0000-000000000001'
  AND password_hash = '';

-- Add tester role to agent_role enum if not already there
DO $$ BEGIN
    ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'tester';
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add test to message_type enum if not already there
DO $$ BEGIN
    ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'test';
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add instructions column to team_members if not already there
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS instructions TEXT DEFAULT '';
