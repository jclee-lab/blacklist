-- Schema Patch: Fix missing columns and data type issues
-- This file will be auto-executed on database initialization

-- ============================================================================
-- 1. Add missing data_source column to blacklist_ips
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE blacklist_ips ADD COLUMN data_source VARCHAR(100);
        RAISE NOTICE 'Added data_source column to blacklist_ips';
    ELSE
        RAISE NOTICE 'data_source column already exists in blacklist_ips';
    END IF;
END $$;

-- Create index on data_source if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'blacklist_ips' AND indexname = 'idx_blacklist_ips_data_source'
    ) THEN
        CREATE INDEX idx_blacklist_ips_data_source ON blacklist_ips(data_source);
        RAISE NOTICE 'Created index on data_source';
    END IF;
END $$;

-- ============================================================================
-- 2. Add missing data_source column to whitelist_ips
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'whitelist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE whitelist_ips ADD COLUMN data_source VARCHAR(100);
        RAISE NOTICE 'Added data_source column to whitelist_ips';
    ELSE
        RAISE NOTICE 'data_source column already exists in whitelist_ips';
    END IF;
END $$;

-- Create index on data_source if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'whitelist_ips' AND indexname = 'idx_whitelist_ips_data_source'
    ) THEN
        CREATE INDEX idx_whitelist_ips_data_source ON whitelist_ips(data_source);
        RAISE NOTICE 'Created index on data_source';
    END IF;
END $$;

-- ============================================================================
-- 3. Update existing rows to populate data_source from source
-- ============================================================================
UPDATE blacklist_ips SET data_source = source WHERE data_source IS NULL;
UPDATE whitelist_ips SET data_source = source WHERE data_source IS NULL;

-- ============================================================================
-- 4. Fix collection_interval type issue (for app compatibility)
-- ============================================================================
-- collection_interval is INTEGER (seconds) in DB
-- App expects: hourly, daily, weekly
-- Solution: Keep as INTEGER, app should convert

-- Add helper function to convert seconds to readable format
CREATE OR REPLACE FUNCTION format_collection_interval(seconds INTEGER)
RETURNS TEXT AS $$
BEGIN
    CASE
        WHEN seconds = 3600 THEN RETURN 'hourly (3600s)';
        WHEN seconds = 21600 THEN RETURN 'every 6 hours (21600s)';
        WHEN seconds = 86400 THEN RETURN 'daily (86400s)';
        WHEN seconds = 604800 THEN RETURN 'weekly (604800s)';
        ELSE RETURN seconds || ' seconds';
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 5. Verify tables exist
-- ============================================================================
DO $$
DECLARE
    missing_tables TEXT[];
    tbl_name TEXT;
BEGIN
    missing_tables := ARRAY[]::TEXT[];

    -- Check critical tables
    FOR tbl_name IN
        SELECT unnest(ARRAY[
            'blacklist_ips',
            'whitelist_ips',
            'collection_credentials',
            'collection_history',
            'collection_status',
            'collection_metrics',
            'collection_stats',
            'monitoring_data',
            'pipeline_metrics',
            'system_logs'
        ])
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl_name) THEN
            missing_tables := array_append(missing_tables, tbl_name);
        END IF;
    END LOOP;

    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE 'All critical tables exist';
    END IF;
END $$;

-- ============================================================================
-- 6. Grant permissions
-- ============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO postgres;

-- ============================================================================
-- Patch completed
-- ============================================================================
