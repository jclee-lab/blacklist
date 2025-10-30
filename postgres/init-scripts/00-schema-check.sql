-- Schema Auto-Fix: Runs on EVERY restart
-- This ensures schema is always correct even if init-scripts were skipped

-- Note: This will be executed alphabetically FIRST (00-*)
-- So it checks/fixes schema before other scripts

-- ============================================================================
-- Auto-add missing data_source column
-- ============================================================================
DO $$
BEGIN
    -- blacklist_ips
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE blacklist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_blacklist_ips_data_source ON blacklist_ips(data_source);
        UPDATE blacklist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '[AUTO-FIX] Added data_source to blacklist_ips';
    END IF;

    -- whitelist_ips
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'whitelist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE whitelist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_whitelist_ips_data_source ON whitelist_ips(data_source);
        UPDATE whitelist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '[AUTO-FIX] Added data_source to whitelist_ips';
    END IF;
END $$;

-- ============================================================================
-- Helper function
-- ============================================================================
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
