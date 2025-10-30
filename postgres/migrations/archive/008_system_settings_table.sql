-- Migration: 006 - System Settings Table
-- Purpose: Store application settings in database instead of .env file
-- Date: 2025-10-13

-- =====================================================
-- Table: system_settings
-- =====================================================
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

    -- Constraints
    CONSTRAINT valid_setting_key CHECK (setting_key ~ '^[A-Z_]+$'),
    CONSTRAINT valid_setting_type CHECK (setting_type IN ('string', 'integer', 'boolean', 'json', 'password')),
    CONSTRAINT valid_category CHECK (category IN ('general', 'collection', 'security', 'notification', 'integration'))
);

-- Create indexes
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);
CREATE INDEX idx_system_settings_active ON system_settings(setting_key, is_active);

-- Create trigger for updated_at
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Insert default settings
-- =====================================================

-- Collection settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category, display_order, is_active)
VALUES
    ('COLLECTION_INTERVAL', '3600', 'integer', 'Auto collection interval in seconds (3600 = 1 hour)', 'collection', 1, true),
    ('DISABLE_AUTO_COLLECTION', 'true', 'boolean', 'Disable automatic collection (manual trigger only)', 'collection', 2, true),
    ('COLLECTION_TIMEOUT', '600', 'integer', 'Collection timeout in seconds (600 = 10 minutes)', 'collection', 3, true),
    ('COLLECTION_RETRY_COUNT', '3', 'integer', 'Number of retries on collection failure', 'collection', 4, true)
ON CONFLICT (setting_key) DO NOTHING;

-- Integration settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category, display_order, is_active)
VALUES
    ('REGTECH_BASE_URL', 'https://regtech.fsec.or.kr', 'string', 'REGTECH API base URL', 'integration', 10, true),
    ('FORTINET_INTEGRATION_ENABLED', 'true', 'boolean', 'Enable FortiGate integration', 'integration', 11, true)
ON CONFLICT (setting_key) DO NOTHING;

-- Security settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category, display_order, is_active)
VALUES
    ('SESSION_TIMEOUT', '3600', 'integer', 'Session timeout in seconds', 'security', 20, true),
    ('MAX_LOGIN_ATTEMPTS', '5', 'integer', 'Maximum login attempts before lockout', 'security', 21, true)
ON CONFLICT (setting_key) DO NOTHING;

-- Notification settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category, display_order, is_active)
VALUES
    ('NOTIFICATION_ENABLED', 'false', 'boolean', 'Enable system notifications', 'notification', 30, true),
    ('ALERT_ON_COLLECTION_FAILURE', 'true', 'boolean', 'Send alert when collection fails', 'notification', 31, true)
ON CONFLICT (setting_key) DO NOTHING;

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to get setting value
CREATE OR REPLACE FUNCTION get_setting(p_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    v_value TEXT;
BEGIN
    SELECT setting_value INTO v_value
    FROM system_settings
    WHERE setting_key = p_key AND is_active = true;

    RETURN v_value;
END;
$$ LANGUAGE plpgsql;

-- Function to update setting value
CREATE OR REPLACE FUNCTION update_setting(p_key VARCHAR, p_value TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE system_settings
    SET setting_value = p_value,
        updated_at = CURRENT_TIMESTAMP
    WHERE setting_key = p_key;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Views
-- =====================================================

-- View: Active settings by category
CREATE OR REPLACE VIEW v_active_settings AS
SELECT
    category,
    setting_key,
    setting_value,
    setting_type,
    description,
    is_encrypted,
    display_order,
    updated_at
FROM system_settings
WHERE is_active = true
ORDER BY category, display_order, setting_key;

-- View: Collection settings
CREATE OR REPLACE VIEW v_collection_settings AS
SELECT
    setting_key,
    setting_value,
    setting_type,
    description,
    updated_at
FROM system_settings
WHERE category = 'collection' AND is_active = true
ORDER BY display_order;

-- =====================================================
-- Permissions
-- =====================================================

GRANT SELECT, INSERT, UPDATE ON system_settings TO postgres;
GRANT USAGE, SELECT ON SEQUENCE system_settings_id_seq TO postgres;
GRANT SELECT ON v_active_settings TO postgres;
GRANT SELECT ON v_collection_settings TO postgres;

-- =====================================================
-- Migration Complete
-- =====================================================

COMMENT ON TABLE system_settings IS 'Application settings stored in database (replaces .env file dependency)';
COMMENT ON COLUMN system_settings.setting_key IS 'Unique setting identifier (uppercase with underscores)';
COMMENT ON COLUMN system_settings.setting_type IS 'Data type: string, integer, boolean, json, password';
COMMENT ON COLUMN system_settings.is_encrypted IS 'Whether the value is encrypted (for sensitive data)';
COMMENT ON COLUMN system_settings.category IS 'Setting category: general, collection, security, notification, integration';
