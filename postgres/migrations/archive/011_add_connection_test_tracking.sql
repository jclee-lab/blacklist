-- Migration: Add connection test tracking columns
-- Purpose: Track connection test results with timestamp

ALTER TABLE collection_credentials
ADD COLUMN IF NOT EXISTS last_connection_test TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_test_result BOOLEAN,
ADD COLUMN IF NOT EXISTS last_test_message TEXT;

COMMENT ON COLUMN collection_credentials.last_connection_test IS 'Last connection test timestamp';
COMMENT ON COLUMN collection_credentials.last_test_result IS 'Last connection test result (true=success, false=failure)';
COMMENT ON COLUMN collection_credentials.last_test_message IS 'Last connection test message';
