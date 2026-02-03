-- ============================================================
-- Blacklist Intelligence Platform - D1 (SQLite) Schema
-- ============================================================
-- Converted from PostgreSQL for Cloudflare D1 compatibility
-- Date: 2026-01-24
-- 
-- Key Conversions Applied:
--   SERIAL PRIMARY KEY     → INTEGER PRIMARY KEY AUTOINCREMENT
--   JSONB                  → TEXT (JSON stored as string)
--   VARCHAR(n)             → TEXT (SQLite ignores length)
--   DECIMAL(n,m)           → REAL
--   BOOLEAN                → INTEGER (0/1)
--   NOW()                  → datetime('now')
--   INTERVAL               → datetime('now', '-30 days')
--   Regex CHECK            → Removed (validate in application)
--   PostgreSQL extensions  → Removed (uuid-ossp, pg_trgm)
--   Triggers               → Simplified syntax
-- ============================================================

-- ============================================================
-- Core Tables
-- ============================================================

-- Blacklist IPs (Main threat intelligence data)
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    reason TEXT,
    source TEXT NOT NULL,
    category TEXT DEFAULT 'unknown',
    confidence_level INTEGER DEFAULT 50 CHECK (confidence_level >= 0 AND confidence_level <= 100),
    detection_count INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,  -- 0=false, 1=true
    country TEXT,
    detection_date TEXT,  -- ISO 8601 date string
    removal_date TEXT,
    last_seen TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    raw_data TEXT DEFAULT '{}',  -- JSON string
    data_source TEXT DEFAULT 'REGTECH',
    UNIQUE(ip_address, source)
);

-- Collection Credentials (Service authentication)
CREATE TABLE IF NOT EXISTS collection_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL UNIQUE,
    username TEXT,
    password TEXT,
    config TEXT DEFAULT '{}',  -- JSON string
    encrypted INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    enabled INTEGER DEFAULT 1,
    collection_interval INTEGER DEFAULT 86400,
    source TEXT DEFAULT 'MANUAL',
    last_collection TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Collection History (Execution logs)
CREATE TABLE IF NOT EXISTS collection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    collection_date TEXT DEFAULT (datetime('now')),
    items_collected INTEGER DEFAULT 0 CHECK (items_collected >= 0),
    success INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time_ms INTEGER DEFAULT 0 CHECK (execution_time_ms >= 0),
    details TEXT DEFAULT '{}'  -- JSON string
);

-- Monitoring Data (Metrics storage)
CREATE TABLE IF NOT EXISTS monitoring_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL CHECK (metric_name != ''),
    metric_value REAL,
    metric_unit TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    additional_data TEXT DEFAULT '{}',
    tags TEXT DEFAULT '{}',
    numeric_value REAL,
    unit TEXT
);

-- System Logs (Application logging)
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL DEFAULT 'INFO' CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    module TEXT,
    function_name TEXT,
    line_number INTEGER,
    timestamp TEXT DEFAULT (datetime('now')),
    additional_context TEXT DEFAULT '{}'
);

-- Collection Status (Service state tracking)
CREATE TABLE IF NOT EXISTS collection_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL UNIQUE,
    enabled INTEGER DEFAULT 1,
    last_run TEXT,
    next_run TEXT,
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'running', 'error', 'disabled')),
    error_count INTEGER DEFAULT 0 CHECK (error_count >= 0),
    success_count INTEGER DEFAULT 0 CHECK (success_count >= 0),
    config TEXT DEFAULT '{}',
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Pipeline Metrics (ETL performance)
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    timestamp TEXT NOT NULL,
    pipeline_name TEXT NOT NULL,
    execution_time REAL DEFAULT 0,
    success_rate REAL DEFAULT 0 CHECK (success_rate >= 0 AND success_rate <= 100),
    error_count INTEGER DEFAULT 0 CHECK (error_count >= 0),
    status TEXT DEFAULT 'unknown',
    metadata TEXT DEFAULT '{}',
    PRIMARY KEY (timestamp, pipeline_name)
);

-- Collection Metrics (Aggregated stats)
CREATE TABLE IF NOT EXISTS collection_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    collection_count INTEGER DEFAULT 0 CHECK (collection_count >= 0),
    success_count INTEGER DEFAULT 0 CHECK (success_count >= 0),
    avg_execution_time REAL DEFAULT 0 CHECK (avg_execution_time >= 0),
    last_collection TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK (success_count <= collection_count)
);

-- Whitelist IPs (Exclusion list)
CREATE TABLE IF NOT EXISTS whitelist_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL UNIQUE,
    reason TEXT,
    source TEXT DEFAULT 'MANUAL',
    country TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Unified IP List (Combined view data)
CREATE TABLE IF NOT EXISTS unified_ip_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    source TEXT,
    category TEXT,
    list_type TEXT DEFAULT 'blacklist',
    reason TEXT,
    confidence_level INTEGER DEFAULT 50,
    detection_count INTEGER DEFAULT 1,
    country TEXT,
    detection_date TEXT,
    removal_date TEXT,
    last_seen TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(ip_address, source)
);

-- FortiGate Pull Logs (Device request tracking)
CREATE TABLE IF NOT EXISTS fortigate_pull_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT,
    device_ip TEXT,
    user_agent TEXT,
    request_path TEXT,
    request_count INTEGER DEFAULT 1,
    ip_count INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    last_request_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- FortiGate Devices (Device registry)
CREATE TABLE IF NOT EXISTS fortigate_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_ip TEXT NOT NULL UNIQUE,
    device_name TEXT,
    device_model TEXT,
    firmware_version TEXT,
    serial_number TEXT,
    location TEXT,
    is_active INTEGER DEFAULT 1,
    last_seen TEXT,
    config TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- System Settings (Key-value configuration)
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    setting_type TEXT DEFAULT 'string',
    is_encrypted INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    category TEXT DEFAULT 'general',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Encrypted Credentials (Secure storage)
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL UNIQUE,
    encrypted_data TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Fortinet Pull Logs (Alternative naming)
CREATE TABLE IF NOT EXISTS fortinet_pull_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_ip TEXT NOT NULL,
    user_agent TEXT,
    request_path TEXT,
    ip_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    response_status INTEGER DEFAULT 200,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Collection Stats (Source aggregation)
CREATE TABLE IF NOT EXISTS collection_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    source TEXT NOT NULL UNIQUE,
    total_ips INTEGER DEFAULT 0,
    last_seen TEXT
);

-- ============================================================
-- Indexes
-- ============================================================

-- blacklist_ips indexes
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_ip ON blacklist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_category ON blacklist_ips(category);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_last_seen ON blacklist_ips(last_seen);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_confidence ON blacklist_ips(confidence_level);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_data_source ON blacklist_ips(data_source);

-- collection_credentials indexes
CREATE INDEX IF NOT EXISTS idx_collection_credentials_service ON collection_credentials(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_credentials_active ON collection_credentials(service_name, is_active);

-- collection_history indexes
CREATE INDEX IF NOT EXISTS idx_collection_history_service ON collection_history(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_history_date ON collection_history(collection_date);
CREATE INDEX IF NOT EXISTS idx_collection_history_success ON collection_history(success);

-- monitoring_data indexes
CREATE INDEX IF NOT EXISTS idx_monitoring_data_metric ON monitoring_data(metric_name);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON monitoring_data(timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_monitoring_unique ON monitoring_data(metric_name, timestamp);

-- system_logs indexes
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);

-- collection_status indexes
CREATE INDEX IF NOT EXISTS idx_collection_status_service ON collection_status(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_status_enabled ON collection_status(enabled);
CREATE INDEX IF NOT EXISTS idx_collection_status_last_run ON collection_status(last_run);

-- pipeline_metrics indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status ON pipeline_metrics(status);

-- collection_metrics indexes
CREATE INDEX IF NOT EXISTS idx_collection_metrics_service ON collection_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_last_collection ON collection_metrics(last_collection);

-- whitelist_ips indexes
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_ip ON whitelist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_source ON whitelist_ips(source);

-- unified_ip_list indexes
CREATE INDEX IF NOT EXISTS idx_unified_ip_list_ip ON unified_ip_list(ip_address);
CREATE INDEX IF NOT EXISTS idx_unified_ip_list_source ON unified_ip_list(source);
CREATE INDEX IF NOT EXISTS idx_unified_ip_list_type ON unified_ip_list(list_type);
CREATE INDEX IF NOT EXISTS idx_unified_ip_list_active ON unified_ip_list(is_active);

-- fortigate_pull_logs indexes
CREATE INDEX IF NOT EXISTS idx_fortigate_pull_logs_ip ON fortigate_pull_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_fortigate_pull_logs_device ON fortigate_pull_logs(device_ip);
CREATE INDEX IF NOT EXISTS idx_fortigate_pull_logs_last_request ON fortigate_pull_logs(last_request_at);

-- fortinet_pull_logs indexes
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_device ON fortinet_pull_logs(device_ip);
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_created ON fortinet_pull_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_status ON fortinet_pull_logs(response_status);

-- system_settings indexes
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);

-- credentials indexes
CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service_name);

-- collection_stats indexes
CREATE INDEX IF NOT EXISTS idx_collection_stats_source ON collection_stats(source);

-- ============================================================
-- Views (D1-compatible)
-- ============================================================

-- Active blacklist view
CREATE VIEW IF NOT EXISTS active_blacklist AS
SELECT 
    ip_address, 
    reason, 
    source, 
    category, 
    confidence_level, 
    country, 
    detection_date, 
    detection_count, 
    last_seen, 
    created_at
FROM blacklist_ips 
WHERE is_active = 1 
ORDER BY last_seen DESC, confidence_level DESC;

-- Collection statistics view
-- Note: PostgreSQL's CASE WHEN true pattern converted to = 1 for SQLite
CREATE VIEW IF NOT EXISTS collection_statistics AS
SELECT 
    service_name,
    COUNT(*) as total_collections,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_collections,
    ROUND(
        CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS REAL) / 
        CAST(COUNT(*) AS REAL) * 100, 
        2
    ) as success_rate,
    SUM(items_collected) as total_items_collected,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(collection_date) as last_collection_date
FROM collection_history 
GROUP BY service_name 
ORDER BY total_collections DESC;

-- Auto-inactive blacklist view
-- Note: PostgreSQL INTERVAL replaced with datetime() function
CREATE VIEW IF NOT EXISTS blacklist_ips_with_auto_inactive AS
SELECT 
    *,
    CASE 
        WHEN last_seen < datetime('now', '-30 days') THEN 0 
        ELSE 1 
    END as auto_active
FROM blacklist_ips;

-- Settings alias view
CREATE VIEW IF NOT EXISTS settings AS 
SELECT * FROM system_settings;

-- ============================================================
-- Triggers (D1-compatible syntax)
-- ============================================================

-- Note: D1 supports triggers but syntax differs from PostgreSQL
-- These triggers update the updated_at column on row updates

CREATE TRIGGER IF NOT EXISTS update_blacklist_ips_updated_at 
    AFTER UPDATE ON blacklist_ips
BEGIN
    UPDATE blacklist_ips SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_collection_credentials_updated_at 
    AFTER UPDATE ON collection_credentials
BEGIN
    UPDATE collection_credentials SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_collection_status_updated_at 
    AFTER UPDATE ON collection_status
BEGIN
    UPDATE collection_status SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_collection_metrics_updated_at 
    AFTER UPDATE ON collection_metrics
BEGIN
    UPDATE collection_metrics SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_whitelist_ips_updated_at 
    AFTER UPDATE ON whitelist_ips
BEGIN
    UPDATE whitelist_ips SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_unified_ip_list_updated_at 
    AFTER UPDATE ON unified_ip_list
BEGIN
    UPDATE unified_ip_list SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_system_settings_updated_at 
    AFTER UPDATE ON system_settings
BEGIN
    UPDATE system_settings SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_credentials_updated_at 
    AFTER UPDATE ON credentials
BEGIN
    UPDATE credentials SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_fortigate_devices_updated_at 
    AFTER UPDATE ON fortigate_devices
BEGIN
    UPDATE fortigate_devices SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================
-- Seed Data
-- ============================================================

-- Default collection credentials
INSERT OR REPLACE INTO collection_credentials (service_name, username, password, config, is_active)
VALUES (
    'REGTECH', 
    '', 
    '', 
    '{"base_url": "https://regtech.fsec.or.kr", "timeout": 30, "max_retries": 3}', 
    1
);

-- Default collection status
INSERT OR IGNORE INTO collection_status (service_name, enabled, status, config) VALUES
    ('REGTECH', 1, 'idle', '{"schedule": "0 */6 * * *", "enabled": true}'),
    ('THREAT_INTEL', 1, 'idle', '{"schedule": "0 */12 * * *", "enabled": false}'),
    ('MALICIOUS_LIST', 1, 'idle', '{"schedule": "0 */24 * * *", "enabled": false}');

-- ============================================================
-- Query Conversion Reference
-- ============================================================
-- 
-- PostgreSQL                          → D1 (SQLite)
-- --------------------------------------------------------
-- column::jsonb                       → json(column)
-- column ->> 'key'                    → json_extract(column, '$.key')
-- column -> 'key'                     → json_extract(column, '$.key')
-- NOW()                               → datetime('now')
-- CURRENT_TIMESTAMP                   → datetime('now')
-- NOW() - INTERVAL '7 days'           → datetime('now', '-7 days')
-- DATE_TRUNC('day', column)           → date(column)
-- EXTRACT(EPOCH FROM column)          → strftime('%s', column)
-- column::text                        → CAST(column AS TEXT)
-- TRUE / FALSE                        → 1 / 0
-- ILIKE                               → LIKE (case-insensitive by default)
-- SIMILAR TO                          → GLOB or LIKE
-- ~ (regex)                           → Not supported (use LIKE/GLOB)
-- COUNT(*) FILTER (WHERE cond)        → SUM(CASE WHEN cond THEN 1 ELSE 0 END)
-- json_object_agg(k, v)               → group_concat + manual parsing
-- ON CONFLICT (col) DO UPDATE         → ON CONFLICT (col) DO UPDATE SET
-- RETURNING *                         → Separate SELECT after INSERT
-- ============================================================
