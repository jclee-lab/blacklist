-- Migration: Add source column to collection_credentials
-- Date: 2025-10-29
-- Purpose: Fix "column source does not exist" error in collector

-- Add source column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'source'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN source VARCHAR(50);

        -- Update existing records with default source based on their data
        -- This is safe because collection_credentials should have specific entries
        UPDATE collection_credentials SET source = 'REGTECH' WHERE source IS NULL;

        -- Make source NOT NULL after setting defaults
        ALTER TABLE collection_credentials ALTER COLUMN source SET NOT NULL;
    END IF;
END $$;

-- Verify column
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'collection_credentials' AND column_name = 'source';
