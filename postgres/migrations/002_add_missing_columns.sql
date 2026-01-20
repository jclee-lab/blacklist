-- Migration: 002_add_missing_columns.sql
-- Date: 2026-01-19
-- Description: Add missing columns required by application code

-- ============================================================
-- 1. collection_credentials.last_collection
-- ============================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'collection_credentials' AND column_name = 'last_collection'
    ) THEN
        ALTER TABLE collection_credentials 
        ADD COLUMN last_collection TIMESTAMP WITHOUT TIME ZONE;
        RAISE NOTICE 'Added: collection_credentials.last_collection';
    END IF;
END $$;

-- ============================================================
-- 2. blacklist_ips.raw_data (JSONB for raw collection data)
-- ============================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'blacklist_ips' AND column_name = 'raw_data'
    ) THEN
        ALTER TABLE blacklist_ips 
        ADD COLUMN raw_data JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added: blacklist_ips.raw_data';
    END IF;
END $$;

-- ============================================================
-- 3. system_settings - add missing columns
-- ============================================================
DO $$ 
BEGIN
    -- setting_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'system_settings' AND column_name = 'setting_type'
    ) THEN
        ALTER TABLE system_settings 
        ADD COLUMN setting_type VARCHAR(20) DEFAULT 'string';
        RAISE NOTICE 'Added: system_settings.setting_type';
    END IF;
    
    -- is_encrypted
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'system_settings' AND column_name = 'is_encrypted'
    ) THEN
        ALTER TABLE system_settings 
        ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added: system_settings.is_encrypted';
    END IF;
    
    -- is_active
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'system_settings' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE system_settings 
        ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added: system_settings.is_active';
    END IF;
    
    -- category
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'system_settings' AND column_name = 'category'
    ) THEN
        ALTER TABLE system_settings 
        ADD COLUMN category VARCHAR(50) DEFAULT 'general';
        RAISE NOTICE 'Added: system_settings.category';
    END IF;
END $$;

-- ============================================================
-- 4. fortinet_pull_logs table (missing entirely)
-- ============================================================
CREATE TABLE IF NOT EXISTS fortinet_pull_logs (
    id SERIAL PRIMARY KEY,
    device_ip VARCHAR(45) NOT NULL,
    user_agent TEXT,
    request_path TEXT,
    ip_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    response_status INTEGER DEFAULT 200,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fortinet_pull_logs
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_device ON fortinet_pull_logs(device_ip);
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_created ON fortinet_pull_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_fortinet_pull_logs_status ON fortinet_pull_logs(response_status);

-- ============================================================
-- 5. Create 'settings' view pointing to system_settings
--    (for code compatibility if any legacy code uses 'settings')
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'settings'
    ) THEN
        CREATE VIEW settings AS SELECT * FROM system_settings;
        RAISE NOTICE 'Created: settings view -> system_settings';
    END IF;
EXCEPTION WHEN duplicate_table THEN
    -- View or table already exists, skip
    NULL;
END $$;

-- ============================================================
-- 6. collection_stats table (missing entirely)
-- ============================================================
CREATE TABLE IF NOT EXISTS collection_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) NOT NULL UNIQUE,
    total_ips INTEGER DEFAULT 0,
    last_seen TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_collection_stats_source ON collection_stats(source);

-- Verification
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count 
    FROM information_schema.columns 
    WHERE table_name IN ('collection_credentials', 'blacklist_ips', 'system_settings', 'fortinet_pull_logs', 'collection_stats');
    
    RAISE NOTICE 'Migration 002 complete. Total columns in affected tables: %', col_count;
END $$;
