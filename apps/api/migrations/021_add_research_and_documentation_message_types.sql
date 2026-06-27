-- Add missing values to message_type DB enums in case they were not fully applied
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'research';
ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'documentation';
