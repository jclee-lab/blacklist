-- Add missing config and encrypted columns to collection_credentials table
-- This migration adds columns required by regtech_config_service

-- Add config column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'collection_credentials' 
        AND column_name = 'config'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN config JSONB;
        RAISE NOTICE 'Added config column to collection_credentials';
    ELSE
        RAISE NOTICE 'config column already exists in collection_credentials';
    END IF;
END $$;

-- Add encrypted column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'collection_credentials' 
        AND column_name = 'encrypted'
    ) THEN
        ALTER TABLE collection_credentials ADD COLUMN encrypted BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added encrypted column to collection_credentials';
    ELSE
        RAISE NOTICE 'encrypted column already exists in collection_credentials';
    END IF;
END $$;

-- Update existing records to have encrypted = false by default
UPDATE collection_credentials 
SET encrypted = false 
WHERE encrypted IS NULL;