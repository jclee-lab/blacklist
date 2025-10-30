-- Add missing is_active column to collection_credentials table
-- This column is required for REGTECH authentication status tracking

-- Check if is_active column exists and add it if missing
DO $$
DECLARE
    column_exists INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_exists
    FROM information_schema.columns 
    WHERE table_name = 'collection_credentials' 
    AND column_name = 'is_active';
    
    IF column_exists = 0 THEN
        ALTER TABLE collection_credentials ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added is_active column to collection_credentials';
    ELSE
        RAISE NOTICE 'is_active column already exists in collection_credentials';
    END IF;
END $$;

-- Update existing records to have is_active = TRUE
UPDATE collection_credentials 
SET is_active = TRUE 
WHERE is_active IS NULL;

-- Add index for better performance on is_active queries
CREATE INDEX IF NOT EXISTS idx_collection_credentials_active 
ON collection_credentials (service_name, is_active);

RAISE NOTICE 'Migration completed: is_active column added to collection_credentials';