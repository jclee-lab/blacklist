-- Migration: 001_schema_fixes.sql
-- Description: Fix schema bugs discovered during E2E testing
-- Date: 2026-01-31
-- Author: AI Testing Session
-- 
-- This migration fixes 4 schema issues found during comprehensive testing:
-- 1. collection_history: Missing collection_type column
-- 2. whitelist_ips: Wrong unique constraint (should include source)
-- 3. whitelist_ips: Missing is_active column
-- 4. blacklist_ips: Missing unique index on ip_address for batch operations

-- ============================================================================
-- FIX 1: Add collection_type column to collection_history
-- ============================================================================
-- The collection history table was missing a column to distinguish
-- between manual triggers and scheduled collection runs.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'collection_history' 
        AND column_name = 'collection_type'
    ) THEN
        ALTER TABLE collection_history 
        ADD COLUMN collection_type VARCHAR(50) DEFAULT 'manual';
        
        COMMENT ON COLUMN collection_history.collection_type IS 
            'Type of collection: manual, scheduled, api_trigger';
    END IF;
END $$;

-- ============================================================================
-- FIX 2: Fix whitelist_ips unique constraint
-- ============================================================================
-- The original constraint was UNIQUE(ip_address) only, but the code uses
-- ON CONFLICT (ip_address, source). This caused upsert failures.

DO $$
BEGIN
    -- Drop the old constraint if it exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'whitelist_unique_ip' 
        AND conrelid = 'whitelist_ips'::regclass
    ) THEN
        ALTER TABLE whitelist_ips DROP CONSTRAINT whitelist_unique_ip;
    END IF;
    
    -- Create new unique index on (ip_address, source)
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'whitelist_unique_ip_source'
    ) THEN
        CREATE UNIQUE INDEX whitelist_unique_ip_source 
        ON whitelist_ips (ip_address, source);
    END IF;
END $$;

-- ============================================================================
-- FIX 3: Add is_active column to whitelist_ips
-- ============================================================================
-- The whitelist table needs soft-delete support via is_active flag.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'whitelist_ips' 
        AND column_name = 'is_active'
    ) THEN
        ALTER TABLE whitelist_ips 
        ADD COLUMN is_active BOOLEAN DEFAULT true;
        
        COMMENT ON COLUMN whitelist_ips.is_active IS 
            'Soft delete flag: true=active, false=deleted';
    END IF;
END $$;

-- ============================================================================
-- FIX 4: Add unique index on blacklist_ips.ip_address
-- ============================================================================
-- Batch add operations need a unique index on ip_address alone
-- for ON CONFLICT handling when source may vary.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'blacklist_ips_ip_unique'
    ) THEN
        CREATE UNIQUE INDEX blacklist_ips_ip_unique 
        ON blacklist_ips (ip_address);
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION QUERIES (run manually to verify migration)
-- ============================================================================
-- SELECT column_name, data_type, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'collection_history' AND column_name = 'collection_type';

-- SELECT indexname FROM pg_indexes WHERE tablename = 'whitelist_ips';

-- SELECT column_name FROM information_schema.columns 
-- WHERE table_name = 'whitelist_ips' AND column_name = 'is_active';

-- SELECT indexname FROM pg_indexes WHERE tablename = 'blacklist_ips';
