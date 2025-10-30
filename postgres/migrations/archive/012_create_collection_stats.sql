-- Migration: Create collection_stats table
-- Purpose: Store collection statistics per source
-- Referenced by: scheduler_service.py, system_api.py, migration_routes.py

CREATE TABLE IF NOT EXISTS collection_stats (
    source VARCHAR(100) PRIMARY KEY,
    total_ips INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,

    -- Constraints
    CONSTRAINT non_negative_total_ips CHECK (total_ips >= 0)
);

-- Create index for timestamp queries
CREATE INDEX IF NOT EXISTS idx_collection_stats_timestamp ON collection_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_stats_last_seen ON collection_stats(last_seen);

-- Initial data for REGTECH and SECUDIUM
INSERT INTO collection_stats (source, total_ips, timestamp, last_seen)
SELECT 'regtech', COUNT(*), NOW(), MAX(last_seen)
FROM blacklist_ips WHERE source = 'regtech'
ON CONFLICT (source) DO NOTHING;

INSERT INTO collection_stats (source, total_ips, timestamp, last_seen)
SELECT 'secudium', COUNT(*), NOW(), MAX(last_seen)
FROM blacklist_ips WHERE source = 'secudium'
ON CONFLICT (source) DO NOTHING;

COMMENT ON TABLE collection_stats IS 'Collection statistics per source (REGTECH, SECUDIUM)';
COMMENT ON COLUMN collection_stats.source IS 'Source name (REGTECH, SECUDIUM)';
COMMENT ON COLUMN collection_stats.total_ips IS 'Total number of IPs from this source';
COMMENT ON COLUMN collection_stats.timestamp IS 'Last statistics update time';
COMMENT ON COLUMN collection_stats.last_seen IS 'Most recent IP last_seen timestamp from this source';
