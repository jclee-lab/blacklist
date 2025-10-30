-- ============================================================================
-- Complete Database Schema Migration
-- ============================================================================
-- Description: Unified migration file containing all schema changes
-- Created: 2025-10-28
-- Author: Blacklist System Team
-- Purpose: Single migration file for complete database initialization
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: Base Tables and Credentials (001, 004, 005, 006)
-- ============================================================================

-- Add encrypted credential support with all necessary columns
DO $$
BEGIN
    -- Add encrypted column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='encrypted') THEN
        ALTER TABLE collection_credentials ADD COLUMN encrypted BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add config column (JSONB for better performance)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='config') THEN
        ALTER TABLE collection_credentials ADD COLUMN config JSONB;
    END IF;

    -- Add updated_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='updated_at') THEN
        ALTER TABLE collection_credentials ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;

    -- Add is_active column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='is_active') THEN
        ALTER TABLE collection_credentials ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;

    -- Add enabled column (backward compatibility)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='enabled') THEN
        ALTER TABLE collection_credentials ADD COLUMN enabled BOOLEAN DEFAULT TRUE;
    END IF;

    -- Add last_collection column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='last_collection') THEN
        ALTER TABLE collection_credentials ADD COLUMN last_collection TIMESTAMP;
    END IF;

    -- Add last_success column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='last_success') THEN
        ALTER TABLE collection_credentials ADD COLUMN last_success BOOLEAN;
    END IF;

    -- Add collected_count column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='collected_count') THEN
        ALTER TABLE collection_credentials ADD COLUMN collected_count INTEGER DEFAULT 0;
    END IF;

    -- Add connection test tracking columns (011, 013)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='last_connection_test') THEN
        ALTER TABLE collection_credentials ADD COLUMN last_connection_test TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='last_test_result') THEN
        ALTER TABLE collection_credentials ADD COLUMN last_test_result BOOLEAN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='collection_credentials' AND column_name='last_test_message') THEN
        ALTER TABLE collection_credentials ADD COLUMN last_test_message TEXT;
    END IF;
END $$;

-- Update existing records
UPDATE collection_credentials SET encrypted = FALSE WHERE encrypted IS NULL;
UPDATE collection_credentials SET is_active = TRUE WHERE is_active IS NULL;
UPDATE collection_credentials SET enabled = is_active WHERE enabled IS NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_collection_credentials_service ON collection_credentials(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_credentials_active ON collection_credentials(service_name, is_active);

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

-- Add comments
COMMENT ON COLUMN collection_credentials.encrypted IS 'Flag indicating if username/password are encrypted';
COMMENT ON COLUMN collection_credentials.config IS 'JSON configuration for service-specific settings';
COMMENT ON COLUMN collection_credentials.updated_at IS 'Timestamp of last update';
COMMENT ON COLUMN collection_credentials.is_active IS 'Authentication status tracking';
COMMENT ON COLUMN collection_credentials.enabled IS 'Collection enabled flag (backward compatibility)';
COMMENT ON COLUMN collection_credentials.last_connection_test IS 'Timestamp of last connection test attempt';
COMMENT ON COLUMN collection_credentials.last_test_result IS 'Result of last connection test (true=success, false=failed)';
COMMENT ON COLUMN collection_credentials.last_test_message IS 'Detailed message from last connection test (error details, etc.)';

-- ============================================================================
-- SECTION 2: Blacklist IP Enhancements (003, 004a)
-- ============================================================================

-- Add REGTECH fields
ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS detection_date DATE;
ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS removal_date DATE;
ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS country VARCHAR(10);

-- Add data source support
ALTER TABLE blacklist_ips
ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'REGTECH'
CHECK (data_source IN ('REGTECH', 'SECUDIUM', 'MANUAL'));

-- Update existing records
UPDATE blacklist_ips SET data_source = 'REGTECH' WHERE data_source IS NULL;

-- Make data_source NOT NULL
ALTER TABLE blacklist_ips ALTER COLUMN data_source SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(data_source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source_active ON blacklist_ips(data_source, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_active ON blacklist_ips(removal_date, is_active) WHERE removal_date IS NOT NULL;

-- Add comments
COMMENT ON COLUMN blacklist_ips.detection_date IS 'IP가 처음 탐지된 날짜';
COMMENT ON COLUMN blacklist_ips.removal_date IS 'IP가 블랙리스트에서 해제될 예정일';
COMMENT ON COLUMN blacklist_ips.country IS 'IP 주소의 국가 코드 (ISO 3166-1 alpha-2)';
COMMENT ON COLUMN blacklist_ips.data_source IS 'Source of blacklist data: REGTECH, SECUDIUM, or MANUAL';

-- ============================================================================
-- SECTION 3: Additional Tables (002, 012)
-- ============================================================================

-- Create pipeline_metrics table
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    execution_time DECIMAL(10,3),
    success_rate DECIMAL(5,2),
    error_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create collection_metrics table
CREATE TABLE IF NOT EXISTS collection_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    avg_execution_time DECIMAL(10,3),
    last_collection TIMESTAMP,
    metadata JSONB
);

-- Create collection_stats table
CREATE TABLE IF NOT EXISTS collection_stats (
    source VARCHAR(100) PRIMARY KEY,
    total_ips INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    CONSTRAINT non_negative_total_ips CHECK (total_ips >= 0)
);

-- Create processed_reports table
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_service ON collection_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_last_collection ON collection_metrics(last_collection);
CREATE INDEX IF NOT EXISTS idx_collection_stats_timestamp ON collection_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_stats_last_seen ON collection_stats(last_seen);
CREATE INDEX IF NOT EXISTS idx_processed_reports_source ON processed_reports(source);
CREATE INDEX IF NOT EXISTS idx_processed_reports_date ON processed_reports(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_processed_reports_source_date ON processed_reports(source, report_date DESC);

-- Add comments
COMMENT ON TABLE pipeline_metrics IS 'CI/CD 파이프라인 성능 메트릭 추적';
COMMENT ON TABLE collection_metrics IS '데이터 수집 서비스 성능 메트릭 추적';
COMMENT ON TABLE collection_stats IS 'Collection statistics per source (REGTECH, SECUDIUM)';
COMMENT ON TABLE processed_reports IS 'Tracks processed reports from external sources to prevent duplicates';

-- ============================================================================
-- SECTION 4: System Settings Table (008)
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) NOT NULL DEFAULT 'string',
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    category VARCHAR(50) DEFAULT 'general',
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_setting_key CHECK (setting_key ~ '^[A-Z_]+$'),
    CONSTRAINT valid_setting_type CHECK (setting_type IN ('string', 'integer', 'boolean', 'json', 'password')),
    CONSTRAINT valid_category CHECK (category IN ('general', 'collection', 'security', 'notification', 'integration'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);
CREATE INDEX IF NOT EXISTS idx_system_settings_active ON system_settings(setting_key, is_active);

-- Create trigger
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category, display_order, is_active)
VALUES
    ('COLLECTION_INTERVAL', '3600', 'integer', 'Auto collection interval in seconds', 'collection', 1, true),
    ('DISABLE_AUTO_COLLECTION', 'true', 'boolean', 'Disable automatic collection', 'collection', 2, true),
    ('COLLECTION_TIMEOUT', '600', 'integer', 'Collection timeout in seconds', 'collection', 3, true),
    ('COLLECTION_RETRY_COUNT', '3', 'integer', 'Number of retries on failure', 'collection', 4, true),
    ('REGTECH_BASE_URL', 'https://regtech.fsec.or.kr', 'string', 'REGTECH API base URL', 'integration', 10, true),
    ('FORTINET_INTEGRATION_ENABLED', 'true', 'boolean', 'Enable FortiGate integration', 'integration', 11, true)
ON CONFLICT (setting_key) DO NOTHING;

COMMENT ON TABLE system_settings IS 'Application settings stored in database';

-- ============================================================================
-- SECTION 5: Views and Functions (004a, 010)
-- ============================================================================

-- Active blacklist view
DROP VIEW IF EXISTS active_blacklist CASCADE;
CREATE VIEW active_blacklist AS
SELECT
    id, ip_address, country, reason, detection_date, removal_date,
    data_source, raw_data, created_at, updated_at
FROM blacklist_ips
WHERE is_active = TRUE AND (removal_date IS NULL OR removal_date > CURRENT_DATE);

-- Blacklist statistics view
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

-- Unified IP list view
CREATE OR REPLACE VIEW unified_ip_list AS
SELECT
    'blacklist' as list_type, id, ip_address, reason, source,
    confidence_level, detection_count, is_active, country,
    detection_date, removal_date, last_seen, created_at, updated_at, raw_data
FROM blacklist_ips
UNION ALL
SELECT
    'whitelist' as list_type, id, ip_address, reason, source,
    NULL, NULL, TRUE, country, NULL, NULL, NULL, created_at, updated_at, NULL
FROM whitelist_ips;

-- Active unified IP list view
CREATE OR REPLACE VIEW active_unified_ip_list AS
SELECT
    list_type, ip_address, reason, source, country,
    detection_date, removal_date, created_at,
    CASE
        WHEN list_type = 'whitelist' THEN TRUE
        WHEN list_type = 'blacklist' AND (removal_date IS NULL OR removal_date > CURRENT_DATE) THEN TRUE
        ELSE FALSE
    END as is_active
FROM unified_ip_list
WHERE (list_type = 'whitelist')
   OR (list_type = 'blacklist' AND is_active = TRUE AND (removal_date IS NULL OR removal_date > CURRENT_DATE));

-- Helper functions
CREATE OR REPLACE FUNCTION get_setting(p_key VARCHAR)
RETURNS TEXT AS $$
DECLARE v_value TEXT;
BEGIN
    SELECT setting_value INTO v_value
    FROM system_settings
    WHERE setting_key = p_key AND is_active = true;
    RETURN v_value;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_setting(p_key VARCHAR, p_value TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE system_settings
    SET setting_value = p_value, updated_at = CURRENT_TIMESTAMP
    WHERE setting_key = p_key;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

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

-- ============================================================================
-- SECTION 6: Initial Data
-- ============================================================================

-- Insert SECUDIUM credentials placeholder
INSERT INTO collection_credentials (service_name, username, password, enabled, collection_interval, last_collection)
VALUES ('SECUDIUM', '${SECUDIUM_USERNAME}', '${SECUDIUM_PASSWORD}', FALSE, 'daily', NULL)
ON CONFLICT (service_name) DO UPDATE
SET username = EXCLUDED.username, password = EXCLUDED.password, updated_at = CURRENT_TIMESTAMP;

-- Initialize collection stats
INSERT INTO collection_stats (source, total_ips, timestamp, last_seen)
SELECT 'regtech', COUNT(*), NOW(), MAX(last_seen)
FROM blacklist_ips WHERE source = 'regtech'
ON CONFLICT (source) DO NOTHING;

INSERT INTO collection_stats (source, total_ips, timestamp, last_seen)
SELECT 'secudium', COUNT(*), NOW(), MAX(last_seen)
FROM blacklist_ips WHERE source = 'secudium'
ON CONFLICT (source) DO NOTHING;

-- ============================================================================
-- SECTION 7: Cleanup and Validation
-- ============================================================================

-- Vacuum tables
VACUUM ANALYZE blacklist_ips;
VACUUM ANALYZE collection_credentials;
VACUUM ANALYZE collection_stats;

-- Validation
DO $$
DECLARE
    invalid_count INTEGER;
    total_records BIGINT;
    regtech_records BIGINT;
    secudium_records BIGINT;
BEGIN
    -- Check for invalid data_source
    SELECT COUNT(*) INTO invalid_count FROM blacklist_ips
    WHERE data_source NOT IN ('REGTECH', 'SECUDIUM', 'MANUAL');

    IF invalid_count > 0 THEN
        RAISE WARNING 'Found % records with invalid data_source', invalid_count;
    END IF;

    -- Get statistics
    SELECT COUNT(*) INTO total_records FROM blacklist_ips;
    SELECT COUNT(*) INTO regtech_records FROM blacklist_ips WHERE data_source = 'REGTECH';
    SELECT COUNT(*) INTO secudium_records FROM blacklist_ips WHERE data_source = 'SECUDIUM';

    RAISE NOTICE '============================================';
    RAISE NOTICE 'Complete Schema Migration Finished';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Total blacklist records: %', total_records;
    RAISE NOTICE 'REGTECH records: %', regtech_records;
    RAISE NOTICE 'SECUDIUM records: %', secudium_records;
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created: pipeline_metrics, collection_metrics,';
    RAISE NOTICE '                collection_stats, processed_reports,';
    RAISE NOTICE '                system_settings';
    RAISE NOTICE 'Views created: active_blacklist, blacklist_statistics,';
    RAISE NOTICE '               unified_ip_list, active_unified_ip_list';
    RAISE NOTICE '============================================';
END;
$$;

COMMIT;

-- ============================================================================
-- End of Migration
-- ============================================================================
