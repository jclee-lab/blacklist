-- ============================================================================
-- Migration V002: Secure Credentials Management
-- ============================================================================
-- Purpose: Enhance security for collection_credentials table
-- Idempotent: Safe to run multiple times
-- ============================================================================

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE '🔒 [V002] Starting credentials security enhancement...';
    RAISE NOTICE '📅 Timestamp: %', NOW();
END $$;

-- ============================================================================
-- Add encryption metadata columns
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '🔐 Adding Encryption Metadata';
    RAISE NOTICE '====================================';

    -- Add is_encrypted flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'is_encrypted'
    ) THEN
        RAISE NOTICE '➕ Adding is_encrypted column';
        ALTER TABLE collection_credentials ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE;
        RAISE NOTICE '✅ is_encrypted column added';
    ELSE
        RAISE NOTICE '✓ is_encrypted column exists';
    END IF;

    -- Add encryption_version
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'encryption_version'
    ) THEN
        RAISE NOTICE '➕ Adding encryption_version column';
        ALTER TABLE collection_credentials ADD COLUMN encryption_version VARCHAR(50);
        RAISE NOTICE '✅ encryption_version column added';
    ELSE
        RAISE NOTICE '✓ encryption_version column exists';
    END IF;

    -- Add last_rotation timestamp
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'collection_credentials' AND column_name = 'last_rotation'
    ) THEN
        RAISE NOTICE '➕ Adding last_rotation column';
        ALTER TABLE collection_credentials ADD COLUMN last_rotation TIMESTAMP;
        RAISE NOTICE '✅ last_rotation column added';
    ELSE
        RAISE NOTICE '✓ last_rotation column exists';
    END IF;

    RAISE NOTICE '✅ Encryption metadata columns verified';
END $$;

-- ============================================================================
-- Create audit log table for credential changes
-- ============================================================================
CREATE TABLE IF NOT EXISTS credential_audit_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'CREATE', 'UPDATE', 'ROTATE', 'DELETE'
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    details JSONB,
    CONSTRAINT fk_credential_audit_service
        FOREIGN KEY (service_name)
        REFERENCES collection_credentials(service_name)
        ON DELETE CASCADE
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_credential_audit_service ON credential_audit_log(service_name);
CREATE INDEX IF NOT EXISTS idx_credential_audit_timestamp ON credential_audit_log(changed_at DESC);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'credential_audit_log') THEN
        RAISE NOTICE '✅ credential_audit_log table created';
    END IF;
END $$;

-- ============================================================================
-- Create trigger to log credential changes
-- ============================================================================
CREATE OR REPLACE FUNCTION log_credential_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO credential_audit_log (
        service_name,
        action,
        changed_by,
        details
    ) VALUES (
        COALESCE(NEW.service_name, OLD.service_name),
        TG_OP,
        current_user,
        jsonb_build_object(
            'old_updated_at', OLD.updated_at,
            'new_updated_at', NEW.updated_at,
            'old_enabled', OLD.enabled,
            'new_enabled', NEW.enabled
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS credential_change_audit ON collection_credentials;

-- Create trigger
CREATE TRIGGER credential_change_audit
AFTER UPDATE ON collection_credentials
FOR EACH ROW
EXECUTE FUNCTION log_credential_change();

DO $$
BEGIN
    RAISE NOTICE '✅ Credential change audit trigger created';
END $$;

-- ============================================================================
-- Create function to check credential expiry
-- ============================================================================
CREATE OR REPLACE FUNCTION get_expired_credentials(days_threshold INTEGER DEFAULT 90)
RETURNS TABLE (
    service_name VARCHAR(255),
    last_update TIMESTAMP,
    days_since_update INTEGER,
    is_enabled BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.service_name,
        cc.updated_at,
        EXTRACT(DAY FROM NOW() - cc.updated_at)::INTEGER,
        cc.enabled
    FROM collection_credentials cc
    WHERE cc.updated_at < NOW() - (days_threshold || ' days')::INTERVAL
    ORDER BY cc.updated_at ASC;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    RAISE NOTICE '✅ get_expired_credentials() function created';
END $$;

-- ============================================================================
-- Create view for credential status
-- ============================================================================
CREATE OR REPLACE VIEW credential_security_status AS
SELECT
    cc.service_name,
    cc.enabled,
    cc.is_encrypted,
    cc.encryption_version,
    cc.last_rotation,
    cc.updated_at,
    CASE
        WHEN cc.updated_at < NOW() - INTERVAL '90 days' THEN '⚠️ EXPIRED'
        WHEN cc.updated_at < NOW() - INTERVAL '60 days' THEN '🟡 WARNING'
        ELSE '✅ OK'
    END AS credential_status,
    EXTRACT(DAY FROM NOW() - cc.updated_at)::INTEGER AS days_since_update
FROM collection_credentials cc
ORDER BY cc.updated_at ASC;

DO $$
BEGIN
    RAISE NOTICE '✅ credential_security_status view created';
END $$;

-- ============================================================================
-- Add security constraints
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '🔒 Adding Security Constraints';
    RAISE NOTICE '====================================';

    -- Ensure service_name is unique and not null
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'collection_credentials_service_name_key'
    ) THEN
        RAISE NOTICE '➕ Adding UNIQUE constraint on service_name';
        ALTER TABLE collection_credentials
        ADD CONSTRAINT collection_credentials_service_name_key UNIQUE (service_name);
    END IF;

    RAISE NOTICE '✅ Security constraints verified';
END $$;

-- ============================================================================
-- Migration Summary
-- ============================================================================
DO $$
DECLARE
    cred_count INTEGER;
    audit_count INTEGER;
    expired_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cred_count FROM collection_credentials;
    SELECT COUNT(*) INTO audit_count FROM credential_audit_log;
    SELECT COUNT(*) INTO expired_count FROM get_expired_credentials(90);

    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE '✅ [V002] Credentials security completed';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Total credentials: %', cred_count;
    RAISE NOTICE 'Audit log entries: %', audit_count;
    RAISE NOTICE 'Expired credentials (90+ days): %', expired_count;
    RAISE NOTICE '';
    RAISE NOTICE 'New features:';
    RAISE NOTICE '  - Encryption metadata tracking';
    RAISE NOTICE '  - Credential change audit log';
    RAISE NOTICE '  - Expiry monitoring function';
    RAISE NOTICE '  - Security status view';
    RAISE NOTICE '====================================';
    RAISE NOTICE '';
END $$;
