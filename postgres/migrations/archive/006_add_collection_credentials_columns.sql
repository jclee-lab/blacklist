-- Migration: Add missing columns to collection_credentials
-- Date: 2025-10-23
-- Purpose: Add enabled and last_collection columns

-- Add enabled column (alias for is_active for backward compatibility)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'enabled'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN enabled BOOLEAN DEFAULT TRUE;
        -- Sync with is_active
        UPDATE collection_credentials SET enabled = is_active;
    END IF;
END $$;

-- Add last_collection column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'last_collection'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN last_collection TIMESTAMP;
    END IF;
END $$;

-- Add last_success column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'last_success'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN last_success BOOLEAN;
    END IF;
END $$;

-- Add collected_count column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'collected_count'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN collected_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Verify columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'collection_credentials'
ORDER BY ordinal_position;
