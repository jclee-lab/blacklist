/**
 * Migration: Add SECUDIUM Data Source Support
 * Version: 004
 * Date: 2025-10-19
 * Author: Blacklist System Team
 *
 * Purpose:
 *   Enable multi-source blacklist data collection by adding data_source column
 *   to blacklist_ips table. This supports both REGTECH and SECUDIUM sources.
 *
 * Changes:
 *   1. Add data_source column to blacklist_ips
 *   2. Add SECUDIUM credentials to collection_credentials
 *   3. Create index for source-based queries
 *   4. Update views to include data_source
 *   5. Add processed_reports tracking table
 */

-- ============================================================================
-- SECTION 1: Add data_source column to blacklist_ips
-- ============================================================================

-- Add data_source column with default 'REGTECH' for existing records
ALTER TABLE blacklist_ips
ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'REGTECH'
CHECK (data_source IN ('REGTECH', 'SECUDIUM', 'MANUAL'));

-- Add comment
COMMENT ON COLUMN blacklist_ips.data_source IS 'Source of blacklist data: REGTECH, SECUDIUM, or MANUAL';

-- Update existing records to have explicit data_source
UPDATE blacklist_ips
SET data_source = 'REGTECH'
WHERE data_source IS NULL;

-- Make data_source NOT NULL after backfilling
ALTER TABLE blacklist_ips
ALTER COLUMN data_source SET NOT NULL;

-- Create index for source-based queries
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source
ON blacklist_ips(data_source);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source_active
ON blacklist_ips(data_source, is_active)
WHERE is_active = TRUE;

-- ============================================================================
-- SECTION 2: SECUDIUM Credentials
-- ============================================================================

-- Insert SECUDIUM credentials (update username/password via environment)
INSERT INTO collection_credentials (service_name, username, password, enabled, collection_interval, last_collection)
VALUES (
    'SECUDIUM',
    '${SECUDIUM_USERNAME}',  -- Replace with actual username
    '${SECUDIUM_PASSWORD}',  -- Replace with actual password
    FALSE,                   -- Disabled by default until credentials are verified
    'daily',
    NULL
)
ON CONFLICT (service_name) DO UPDATE
SET username = EXCLUDED.username,
    password = EXCLUDED.password,
    updated_at = CURRENT_TIMESTAMP;

-- Add comment
COMMENT ON TABLE collection_credentials IS 'Credentials and settings for external data sources (REGTECH, SECUDIUM)';

-- ============================================================================
-- SECTION 3: Processed Reports Tracking Table
-- ============================================================================

-- Create table to track which reports have been processed
-- This prevents duplicate processing and enables incremental collection
CREATE TABLE IF NOT EXISTS processed_reports (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    report_id VARCHAR(100) NOT NULL,
    report_date DATE,
    filename VARCHAR(255),
    records_count INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    UNIQUE(source, report_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_processed_reports_source ON processed_reports(source);
CREATE INDEX IF NOT EXISTS idx_processed_reports_date ON processed_reports(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_processed_reports_source_date ON processed_reports(source, report_date DESC);

-- Add comments
COMMENT ON TABLE processed_reports IS 'Tracks processed reports from external sources to prevent duplicates';
COMMENT ON COLUMN processed_reports.source IS 'Data source: REGTECH, SECUDIUM';
COMMENT ON COLUMN processed_reports.report_id IS 'External report ID from source system';
COMMENT ON COLUMN processed_reports.metadata IS 'Additional report metadata (title, author, etc.)';

-- ============================================================================
-- SECTION 4: Update Views to Include data_source
-- ============================================================================

-- Drop and recreate active_blacklist view with data_source
DROP VIEW IF EXISTS active_blacklist CASCADE;

CREATE VIEW active_blacklist AS
SELECT
    id,
    ip_address,
    country,
    reason,
    detection_date,
    removal_date,
    data_source,
    raw_data,
    created_at,
    updated_at
FROM blacklist_ips
WHERE is_active = TRUE
  AND (removal_date IS NULL OR removal_date > CURRENT_DATE);

COMMENT ON VIEW active_blacklist IS 'Active blacklist IPs from all sources (REGTECH, SECUDIUM, MANUAL)';

-- Drop and recreate blacklist_statistics view with source breakdown
DROP VIEW IF EXISTS blacklist_statistics CASCADE;

CREATE VIEW blacklist_statistics AS
SELECT
    COUNT(*) as total_ips,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_ips,
    COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_ips,
    COUNT(*) FILTER (WHERE data_source = 'REGTECH') as regtech_ips,
    COUNT(*) FILTER (WHERE data_source = 'SECUDIUM') as secudium_ips,
    COUNT(*) FILTER (WHERE data_source = 'MANUAL') as manual_ips,
    COUNT(DISTINCT country) as countries_count,
    MIN(detection_date) as earliest_detection,
    MAX(detection_date) as latest_detection,
    COUNT(*) FILTER (WHERE detection_date = CURRENT_DATE) as today_detections
FROM blacklist_ips;

COMMENT ON VIEW blacklist_statistics IS 'Statistics for blacklist IPs with source breakdown';

-- Update fortinet_active_ips view to include data_source
DROP VIEW IF EXISTS fortinet_active_ips CASCADE;

CREATE VIEW fortinet_active_ips AS
SELECT
    ip_address::text as ip,
    country,
    reason,
    detection_date,
    removal_date,
    data_source,
    CASE
        WHEN removal_date IS NOT NULL THEN removal_date - detection_date
        ELSE NULL
    END as days_active
FROM blacklist_ips
WHERE is_active = TRUE
  AND (removal_date IS NULL OR removal_date > CURRENT_DATE)
ORDER BY detection_date DESC;

COMMENT ON VIEW fortinet_active_ips IS 'Active IPs formatted for FortiGate firewall integration';

-- ============================================================================
-- SECTION 5: Data Quality Functions
-- ============================================================================

-- Function to check for duplicate IPs across sources
CREATE OR REPLACE FUNCTION check_duplicate_ips()
RETURNS TABLE (
    ip_address INET,
    sources TEXT[],
    detection_dates DATE[],
    conflict BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.ip_address,
        array_agg(DISTINCT b.data_source) as sources,
        array_agg(DISTINCT b.detection_date) as detection_dates,
        (COUNT(DISTINCT b.data_source) > 1) as conflict
    FROM blacklist_ips b
    WHERE b.is_active = TRUE
    GROUP BY b.ip_address
    HAVING COUNT(DISTINCT b.data_source) > 1
    ORDER BY b.ip_address;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_duplicate_ips() IS 'Find IPs present in multiple data sources (for validation)';

-- Function to get source-specific statistics
CREATE OR REPLACE FUNCTION get_source_statistics(source_name VARCHAR)
RETURNS TABLE (
    total_ips BIGINT,
    active_ips BIGINT,
    inactive_ips BIGINT,
    today_detections BIGINT,
    countries_count BIGINT,
    earliest_detection DATE,
    latest_detection DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_ips,
        COUNT(*) FILTER (WHERE is_active = TRUE)::BIGINT as active_ips,
        COUNT(*) FILTER (WHERE is_active = FALSE)::BIGINT as inactive_ips,
        COUNT(*) FILTER (WHERE detection_date = CURRENT_DATE)::BIGINT as today_detections,
        COUNT(DISTINCT country)::BIGINT as countries_count,
        MIN(detection_date) as earliest_detection,
        MAX(detection_date) as latest_detection
    FROM blacklist_ips
    WHERE data_source = source_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_source_statistics(VARCHAR) IS 'Get statistics for a specific data source';

-- ============================================================================
-- SECTION 6: Validation and Cleanup
-- ============================================================================

-- Validate data integrity
DO $$
DECLARE
    invalid_count INTEGER;
BEGIN
    -- Check for invalid data_source values
    SELECT COUNT(*) INTO invalid_count
    FROM blacklist_ips
    WHERE data_source NOT IN ('REGTECH', 'SECUDIUM', 'MANUAL');

    IF invalid_count > 0 THEN
        RAISE WARNING 'Found % records with invalid data_source', invalid_count;
    END IF;

    -- Check for NULL data_source values
    SELECT COUNT(*) INTO invalid_count
    FROM blacklist_ips
    WHERE data_source IS NULL;

    IF invalid_count > 0 THEN
        RAISE WARNING 'Found % records with NULL data_source', invalid_count;
    END IF;

    RAISE NOTICE 'Data validation complete';
END;
$$;

-- ============================================================================
-- SECTION 7: Grant Permissions
-- ============================================================================

-- Grant permissions on new table
GRANT SELECT, INSERT, UPDATE, DELETE ON processed_reports TO postgres;
GRANT USAGE, SELECT ON SEQUENCE processed_reports_id_seq TO postgres;

-- Grant permissions on updated views
GRANT SELECT ON active_blacklist TO postgres;
GRANT SELECT ON blacklist_statistics TO postgres;
GRANT SELECT ON fortinet_active_ips TO postgres;

-- Grant execute on new functions
GRANT EXECUTE ON FUNCTION check_duplicate_ips() TO postgres;
GRANT EXECUTE ON FUNCTION get_source_statistics(VARCHAR) TO postgres;

-- ============================================================================
-- SECTION 8: Verification Queries
-- ============================================================================

-- Print migration summary
DO $$
DECLARE
    total_records BIGINT;
    regtech_records BIGINT;
    secudium_records BIGINT;
    manual_records BIGINT;
BEGIN
    SELECT COUNT(*) INTO total_records FROM blacklist_ips;
    SELECT COUNT(*) INTO regtech_records FROM blacklist_ips WHERE data_source = 'REGTECH';
    SELECT COUNT(*) INTO secudium_records FROM blacklist_ips WHERE data_source = 'SECUDIUM';
    SELECT COUNT(*) INTO manual_records FROM blacklist_ips WHERE data_source = 'MANUAL';

    RAISE NOTICE '============================================';
    RAISE NOTICE 'Migration 004: SECUDIUM Support Complete';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Total blacklist records: %', total_records;
    RAISE NOTICE 'REGTECH records: %', regtech_records;
    RAISE NOTICE 'SECUDIUM records: %', secudium_records;
    RAISE NOTICE 'MANUAL records: %', manual_records;
    RAISE NOTICE '';
    RAISE NOTICE 'New tables: processed_reports';
    RAISE NOTICE 'Updated views: active_blacklist, blacklist_statistics, fortinet_active_ips';
    RAISE NOTICE 'New functions: check_duplicate_ips(), get_source_statistics()';
    RAISE NOTICE '============================================';
END;
$$;

-- Sample verification queries (commented out)
-- SELECT * FROM blacklist_statistics;
-- SELECT * FROM check_duplicate_ips();
-- SELECT * FROM get_source_statistics('REGTECH');
-- SELECT * FROM get_source_statistics('SECUDIUM');
-- SELECT * FROM collection_credentials WHERE service_name IN ('REGTECH', 'SECUDIUM');
