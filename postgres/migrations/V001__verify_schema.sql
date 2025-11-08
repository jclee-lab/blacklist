-- ============================================================================
-- Migration V001: Schema Verification and Update
-- ============================================================================
-- Purpose: Verify schema integrity and update if needed
-- Idempotent: Safe to run multiple times
-- ============================================================================

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE '🔍 [V001] Starting schema verification...';
    RAISE NOTICE '📅 Timestamp: %', NOW();
END $$;

-- ============================================================================
-- Verify Core Tables
-- ============================================================================
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '📋 Verifying Core Tables';
    RAISE NOTICE '====================================';

    -- Check blacklist_ips
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blacklist_ips') THEN
        RAISE EXCEPTION '❌ blacklist_ips table missing! Run init-scripts first.';
    END IF;

    -- Check whitelist_ips
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'whitelist_ips') THEN
        RAISE EXCEPTION '❌ whitelist_ips table missing! Run init-scripts first.';
    END IF;

    -- Check collection_credentials
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'collection_credentials') THEN
        RAISE EXCEPTION '❌ collection_credentials table missing! Run init-scripts first.';
    END IF;

    -- Count all tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public';

    RAISE NOTICE '✅ Core tables verified';
    RAISE NOTICE 'Total tables: %', table_count;
END $$;

-- ============================================================================
-- Verify data_source Columns
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '🔍 Verifying data_source Columns';
    RAISE NOTICE '====================================';

    -- Check blacklist_ips.data_source
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'data_source'
    ) THEN
        RAISE NOTICE '➕ Adding data_source to blacklist_ips';
        ALTER TABLE blacklist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_blacklist_ips_data_source ON blacklist_ips(data_source);
        UPDATE blacklist_ips SET data_source = source WHERE data_source IS NULL;
    ELSE
        RAISE NOTICE '✓ blacklist_ips.data_source exists';
    END IF;

    -- Check whitelist_ips.data_source
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'whitelist_ips' AND column_name = 'data_source'
    ) THEN
        RAISE NOTICE '➕ Adding data_source to whitelist_ips';
        ALTER TABLE whitelist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_whitelist_ips_data_source ON whitelist_ips(data_source);
        UPDATE whitelist_ips SET data_source = source WHERE data_source IS NULL;
    ELSE
        RAISE NOTICE '✓ whitelist_ips.data_source exists';
    END IF;

    RAISE NOTICE '✅ data_source columns verified';
END $$;

-- ============================================================================
-- Verify Indexes
-- ============================================================================
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '📇 Verifying Indexes';
    RAISE NOTICE '====================================';

    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    IF index_count < 30 THEN
        RAISE WARNING '⚠️ Only % indexes found (expected 30+)', index_count;
    ELSE
        RAISE NOTICE '✅ % indexes found', index_count;
    END IF;
END $$;

-- ============================================================================
-- Verify Views
-- ============================================================================
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '👁️ Verifying Views';
    RAISE NOTICE '====================================';

    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%';

    IF view_count < 7 THEN
        RAISE WARNING '⚠️ Only % views found (expected 7+)', view_count;
    ELSE
        RAISE NOTICE '✅ % views found', view_count;
    END IF;
END $$;

-- ============================================================================
-- Migration Summary
-- ============================================================================
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_schema = 'public';
    SELECT COUNT(*) INTO index_count FROM pg_indexes WHERE schemaname = 'public';
    SELECT COUNT(*) INTO view_count FROM information_schema.views WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%';

    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '✅ [V001] Schema verification completed';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Tables:  %', table_count;
    RAISE NOTICE 'Indexes: %', index_count;
    RAISE NOTICE 'Views:   %', view_count;
    RAISE NOTICE '====================================';
    RAISE NOTICE '';
END $$;
