-- Migration 003: Add display_order column to system_settings
-- Required by settings_service.py for UI ordering
-- Applied: 2026-01-21

ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

COMMENT ON COLUMN system_settings.display_order IS 'UI display order within category';
