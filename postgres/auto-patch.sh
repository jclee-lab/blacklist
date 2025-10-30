#!/bin/bash
# Auto-patch script that runs on EVERY PostgreSQL restart
# Called from docker-compose command override

set -e

echo "[AUTO-PATCH] Starting PostgreSQL with auto-fix..."

# Start PostgreSQL in background
docker-entrypoint.sh postgres &
PG_PID=$!

# Wait for PostgreSQL to be ready
until pg_isready -U postgres -d blacklist >/dev/null 2>&1; do
    echo "[AUTO-PATCH] Waiting for PostgreSQL..."
    sleep 1
done

echo "[AUTO-PATCH] PostgreSQL ready, applying schema fixes..."

# Apply schema fixes
psql -U postgres -d blacklist <<'EOSQL'
-- Auto-add data_source columns if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE blacklist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX idx_blacklist_ips_data_source ON blacklist_ips(data_source);
        UPDATE blacklist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '[AUTO-PATCH] Added data_source to blacklist_ips';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'whitelist_ips' AND column_name = 'data_source'
    ) THEN
        ALTER TABLE whitelist_ips ADD COLUMN data_source VARCHAR(100);
        CREATE INDEX idx_whitelist_ips_data_source ON whitelist_ips(data_source);
        UPDATE whitelist_ips SET data_source = source WHERE data_source IS NULL;
        RAISE NOTICE '[AUTO-PATCH] Added data_source to whitelist_ips';
    END IF;
END $$;

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
EOSQL

echo "[AUTO-PATCH] Schema fixes applied successfully"

# Keep PostgreSQL running in foreground
wait $PG_PID
