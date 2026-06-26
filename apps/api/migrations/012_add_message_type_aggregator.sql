-- Add aggregator to message_type enum for parallel agent output
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'aggregator';
