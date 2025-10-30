-- Migration: Extend collection_credentials table
-- Date: 2025-10-28
-- Purpose: Add collection management columns

-- Add collection_interval column (default 1 day = 86400 seconds)
ALTER TABLE collection_credentials ADD COLUMN IF NOT EXISTS collection_interval INTEGER DEFAULT 86400;
COMMENT ON COLUMN collection_credentials.collection_interval IS 'Collection interval in seconds (default: 86400 = 1 day)';

-- Add enabled column (alias for is_active for backward compatibility)
ALTER TABLE collection_credentials ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;

-- Add expiry_date column
ALTER TABLE collection_credentials ADD COLUMN IF NOT EXISTS expiry_date DATE;
COMMENT ON COLUMN collection_credentials.expiry_date IS 'Credential expiration date (NULL = no expiry)';

-- Add last_collection column
ALTER TABLE collection_credentials ADD COLUMN IF NOT EXISTS last_collection TIMESTAMP;

-- Sync enabled with is_active for existing rows
UPDATE collection_credentials SET enabled = is_active WHERE enabled IS NULL;

-- Create auto-disable trigger function
CREATE OR REPLACE FUNCTION auto_disable_expired_credentials()
RETURNS void AS $$
BEGIN
    UPDATE collection_credentials
    SET enabled = FALSE
    WHERE expiry_date IS NOT NULL
      AND expiry_date < CURRENT_DATE
      AND enabled = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create helper function for formatting collection interval
CREATE OR REPLACE FUNCTION format_collection_interval(seconds INTEGER)
RETURNS TEXT AS $$
BEGIN
    IF seconds IS NULL THEN
        RETURN 'Not configured';
    ELSIF seconds < 60 THEN
        RETURN seconds || ' seconds';
    ELSIF seconds < 3600 THEN
        RETURN (seconds / 60) || ' minutes';
    ELSE
        RETURN (seconds / 3600) || ' hours';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

\echo 'Collection credentials extended schema applied'
