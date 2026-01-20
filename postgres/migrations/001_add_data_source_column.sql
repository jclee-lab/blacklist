-- Migration: Add data_source column to blacklist_ips
-- Date: 2026-01-19
-- Description: Collector expects data_source column for source tracking

ALTER TABLE blacklist_ips 
ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'REGTECH';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_data_source 
ON blacklist_ips(data_source);

-- Update existing rows to use source value if data_source is null
UPDATE blacklist_ips 
SET data_source = source 
WHERE data_source IS NULL OR data_source = 'REGTECH';
