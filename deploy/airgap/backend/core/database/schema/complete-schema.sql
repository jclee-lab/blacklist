-- Blacklist Management System - Complete Database Schema
-- REGTECH Blacklist Intelligence Platform
-- Version: 3.1.0 (January 2026)
-- FIXES: collection_type, whitelist_ips, blacklist_ips_ip_unique

SELECT 'CREATE DATABASE blacklist'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'blacklist')\gexec

\c blacklist;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. blacklist_ips
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,
    source VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT 'unknown',
    confidence_level INTEGER DEFAULT 50 CHECK (confidence_level >= 0 AND confidence_level <= 100),
    detection_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    country VARCHAR(10),
    detection_date DATE,
    removal_date DATE,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_ip_source UNIQUE(ip_address, source),
    CONSTRAINT valid_ip_format CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$'),
    CONSTRAINT detection_before_removal CHECK (removal_date IS NULL OR detection_date <= removal_date)
);

-- 2. whitelist_ips (NEW - was missing from schema)
CREATE TABLE IF NOT EXISTS whitelist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,
    source VARCHAR(100) DEFAULT 'manual',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_whitelist_ip_format CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$')
);

-- 3. collection_credentials
CREATE TABLE IF NOT EXISTS collection_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(255),
    password TEXT,
    config JSONB DEFAULT '{}',
    encrypted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_service_name CHECK (service_name ~ '^[A-Z_]+$')
);

-- 4. collection_history (FIXED: added collection_type)
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_type VARCHAR(50) DEFAULT 'manual',
    collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items_collected INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    details JSONB DEFAULT '{}',

    CONSTRAINT positive_items CHECK (items_collected >= 0),
    CONSTRAINT positive_execution_time CHECK (execution_time_ms >= 0)
);

-- 5. monitoring_data
CREATE TABLE IF NOT EXISTS monitoring_data (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    numeric_value DECIMAL(12,4),
    unit VARCHAR(20),

    CONSTRAINT valid_metric_name CHECK (metric_name != '')
);

-- 6. system_logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_context JSONB DEFAULT '{}',

    CONSTRAINT valid_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- 7. collection_status
CREATE TABLE IF NOT EXISTS collection_status (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    status VARCHAR(50) DEFAULT 'idle',
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('idle', 'running', 'error', 'disabled')),
    CONSTRAINT non_negative_counts CHECK (error_count >= 0 AND success_count >= 0)
);

-- 8. pipeline_metrics
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    timestamp TIMESTAMP NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    execution_time DECIMAL(10,3) DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'unknown',
    metadata JSONB DEFAULT '{}',

    PRIMARY KEY (timestamp, pipeline_name),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT non_negative_error_count CHECK (error_count >= 0)
);

-- 9. collection_metrics
CREATE TABLE IF NOT EXISTS collection_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    avg_execution_time DECIMAL(10,3) DEFAULT 0,
    last_collection TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT non_negative_metrics CHECK (
        collection_count >= 0 AND
        success_count >= 0 AND
        avg_execution_time >= 0
    ),
    CONSTRAINT success_not_exceed_total CHECK (success_count <= collection_count)
);

-- INDEXES: blacklist_ips
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_ip ON blacklist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_category ON blacklist_ips(category);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_last_seen ON blacklist_ips(last_seen);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_confidence ON blacklist_ips(confidence_level);
CREATE UNIQUE INDEX IF NOT EXISTS blacklist_ips_ip_unique ON blacklist_ips(ip_address);

-- INDEXES: whitelist_ips (NEW)
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_ip ON whitelist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_source ON whitelist_ips(source);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_active ON whitelist_ips(is_active);
CREATE UNIQUE INDEX IF NOT EXISTS whitelist_unique_ip_source ON whitelist_ips(ip_address, source);

-- INDEXES: collection_credentials
CREATE INDEX IF NOT EXISTS idx_collection_credentials_service ON collection_credentials(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_credentials_active ON collection_credentials(service_name, is_active);

-- INDEXES: collection_history
CREATE INDEX IF NOT EXISTS idx_collection_history_service ON collection_history(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_history_date ON collection_history(collection_date);
CREATE INDEX IF NOT EXISTS idx_collection_history_success ON collection_history(success);
CREATE INDEX IF NOT EXISTS idx_collection_history_type ON collection_history(collection_type);

-- INDEXES: monitoring_data
CREATE INDEX IF NOT EXISTS idx_monitoring_data_metric ON monitoring_data(metric_name);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON monitoring_data(timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_monitoring_unique ON monitoring_data (metric_name, timestamp);

-- INDEXES: system_logs
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);

-- INDEXES: collection_status
CREATE INDEX IF NOT EXISTS idx_collection_status_service ON collection_status(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_status_enabled ON collection_status(enabled);
CREATE INDEX IF NOT EXISTS idx_collection_status_last_run ON collection_status(last_run);

-- INDEXES: pipeline_metrics
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status ON pipeline_metrics(status);

-- INDEXES: collection_metrics
CREATE INDEX IF NOT EXISTS idx_collection_metrics_service ON collection_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_last_collection ON collection_metrics(last_collection);

-- VIEWS
CREATE OR REPLACE VIEW active_blacklist AS
SELECT ip_address, reason, source, category, confidence_level, country,
       detection_date, detection_count, last_seen, created_at
FROM blacklist_ips WHERE is_active = TRUE
ORDER BY last_seen DESC, confidence_level DESC;

CREATE OR REPLACE VIEW active_whitelist AS
SELECT ip_address, reason, source, created_at
FROM whitelist_ips WHERE is_active = TRUE
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW collection_statistics AS
SELECT service_name, COUNT(*) as total_collections,
       COUNT(CASE WHEN success = true THEN 1 END) as successful_collections,
       ROUND(COUNT(CASE WHEN success = true THEN 1 END)::decimal / COUNT(*)::decimal * 100, 2) as success_rate,
       SUM(items_collected) as total_items_collected,
       AVG(execution_time_ms) as avg_execution_time_ms,
       MAX(collection_date) as last_collection_date
FROM collection_history GROUP BY service_name ORDER BY total_collections DESC;

CREATE OR REPLACE VIEW recent_activity AS
SELECT 'collection' as activity_type, service_name as source, items_collected as count,
       collection_date as timestamp, success as status
FROM collection_history WHERE collection_date >= NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 'blacklist_update' as activity_type, source, 1 as count,
       updated_at as timestamp, true as status
FROM blacklist_ips WHERE updated_at >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- TRIGGERS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_blacklist_ips_updated_at ON blacklist_ips;
CREATE TRIGGER update_blacklist_ips_updated_at BEFORE UPDATE ON blacklist_ips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_whitelist_ips_updated_at ON whitelist_ips;
CREATE TRIGGER update_whitelist_ips_updated_at BEFORE UPDATE ON whitelist_ips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_collection_credentials_updated_at ON collection_credentials;
CREATE TRIGGER update_collection_credentials_updated_at BEFORE UPDATE ON collection_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_collection_status_updated_at ON collection_status;
CREATE TRIGGER update_collection_status_updated_at BEFORE UPDATE ON collection_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_collection_metrics_updated_at ON collection_metrics;
CREATE TRIGGER update_collection_metrics_updated_at BEFORE UPDATE ON collection_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- DEFAULT DATA
INSERT INTO collection_credentials (service_name, username, password, config, is_active)
VALUES ('REGTECH', '', '', '{"base_url": "https://regtech.fsec.or.kr", "timeout": 30, "max_retries": 3}', TRUE)
ON CONFLICT (service_name) DO UPDATE SET config = EXCLUDED.config, is_active = EXCLUDED.is_active, updated_at = NOW();

INSERT INTO collection_status (service_name, enabled, status, config) VALUES
('REGTECH', TRUE, 'idle', '{"schedule": "0 */6 * * *", "enabled": true}'),
('THREAT_INTEL', TRUE, 'idle', '{"schedule": "0 */12 * * *", "enabled": false}'),
('MALICIOUS_LIST', TRUE, 'idle', '{"schedule": "0 */24 * * *", "enabled": false}')
ON CONFLICT (service_name) DO NOTHING;

-- PERMISSIONS
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

DO $$ BEGIN
    RAISE NOTICE 'Blacklist Database Schema v3.1.0 initialized';
    RAISE NOTICE 'Tables: % | Indexes: % | Views: % | Triggers: %',
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'),
        (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public'),
        (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public');
END $$;
