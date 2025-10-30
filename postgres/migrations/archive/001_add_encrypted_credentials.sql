-- Migration: Add encrypted credential support
-- Date: 2025-09-08
-- Purpose: Enable encrypted credential storage with configuration JSON

-- Add encrypted flag and config JSON to collection_credentials table
DO $$ 
BEGIN
    -- Add encrypted column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='collection_credentials' AND column_name='encrypted') THEN
        ALTER TABLE collection_credentials 
        ADD COLUMN encrypted BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add config column if it doesn't exist  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='collection_credentials' AND column_name='config') THEN
        ALTER TABLE collection_credentials 
        ADD COLUMN config TEXT;
    END IF;
    
    -- Add updated_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='collection_credentials' AND column_name='updated_at') THEN
        ALTER TABLE collection_credentials 
        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Update existing records to set encrypted flag
UPDATE collection_credentials 
SET encrypted = FALSE 
WHERE encrypted IS NULL;

-- Create index for service_name lookups
CREATE INDEX IF NOT EXISTS idx_collection_credentials_service 
ON collection_credentials(service_name);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_collection_credentials_updated_at ON collection_credentials;
CREATE TRIGGER update_collection_credentials_updated_at 
    BEFORE UPDATE ON collection_credentials 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment for documentation
COMMENT ON COLUMN collection_credentials.encrypted IS 'Flag indicating if username/password are encrypted';
COMMENT ON COLUMN collection_credentials.config IS 'JSON configuration for service-specific settings';
COMMENT ON COLUMN collection_credentials.updated_at IS 'Timestamp of last update';