-- Migration: Add connection test tracking columns to collection_credentials
-- Date: 2025-10-28
-- Purpose: Fix schema error - add missing columns for connection test tracking

-- Add connection test tracking columns
ALTER TABLE collection_credentials
ADD COLUMN IF NOT EXISTS last_connection_test TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_test_result BOOLEAN,
ADD COLUMN IF NOT EXISTS last_test_message TEXT;

-- Add comment
COMMENT ON COLUMN collection_credentials.last_connection_test IS 'Timestamp of last connection test attempt';
COMMENT ON COLUMN collection_credentials.last_test_result IS 'Result of last connection test (true=success, false=failed)';
COMMENT ON COLUMN collection_credentials.last_test_message IS 'Detailed message from last connection test (error details, etc.)';

-- Verify
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'collection_credentials'
  AND column_name LIKE 'last_%'
ORDER BY column_name;
