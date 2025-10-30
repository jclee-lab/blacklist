-- Migration: Add data_source columns
-- Date: 2025-10-28
-- Purpose: Track data source for each IP entry

-- Add data_source column to blacklist_ips
ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS data_source VARCHAR(50);
COMMENT ON COLUMN blacklist_ips.data_source IS 'Source of the blacklist data (FMG, CSV, Manual, etc.)';

-- Add data_source column to whitelist_ips
ALTER TABLE whitelist_ips ADD COLUMN IF NOT EXISTS data_source VARCHAR(50);
COMMENT ON COLUMN whitelist_ips.data_source IS 'Source of the whitelist data (FMG, CSV, Manual, etc.)';

\echo 'Data source columns added'
