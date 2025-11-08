-- ============================================================================
-- Schema Auto-Validation and Fix
-- ============================================================================
-- Purpose: Ensures schema integrity on EVERY container restart
-- Execution: Runs FIRST (00-*) in alphabetical order
-- Safety: Idempotent (safe to run multiple times)
-- ============================================================================

-- Log startup
DO $$
BEGIN
    RAISE NOTICE '🔍 [SCHEMA-CHECK] Starting schema validation...';
    RAISE NOTICE '📅 Timestamp: %', NOW();
END $$;

-- ============================================================================
-- SECTION 1: Auto-add missing data_source columns
-- ============================================================================
DO $$
BEGIN
    -- blacklist_ips table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'data_source'
    ) THEN
        RAISE NOTICE '➕ Adding data_source column to blacklist_ips';
        ALTER TABLE blacklist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_blacklist_ips_data_source ON blacklist_ips(data_source);
        UPDATE blacklist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '✅ Added data_source to blacklist_ips';
    ELSE
        RAISE NOTICE '✓ blacklist_ips.data_source already exists';
    END IF;

    -- whitelist_ips table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'whitelist_ips' AND column_name = 'data_source'
    ) THEN
        RAISE NOTICE '➕ Adding data_source column to whitelist_ips';
        ALTER TABLE whitelist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_whitelist_ips_data_source ON whitelist_ips(data_source);
        UPDATE whitelist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '✅ Added data_source to whitelist_ips';
    ELSE
        RAISE NOTICE '✓ whitelist_ips.data_source already exists';
    END IF;
END $$;

-- ============================================================================
-- SECTION 2: Helper Functions
-- ============================================================================

-- Format collection interval (seconds to human-readable)
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
-- SECTION 3: Schema Validation Summary
-- ============================================================================
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    view_count INTEGER;
BEGIN
    -- Count schema objects
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public';

    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public';

    -- Display summary
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '✅ Schema validation completed';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Tables:  %', table_count;
    RAISE NOTICE 'Indexes: %', index_count;
    RAISE NOTICE 'Views:   %', view_count;
    RAISE NOTICE '====================================';
    RAISE NOTICE '';
END $$;
