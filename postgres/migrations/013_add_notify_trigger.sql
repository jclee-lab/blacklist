-- Migration 013: Add NOTIFY trigger for real-time FortiManager Push
--
-- Purpose:
--   - blacklist_ips 테이블 변경 시 NOTIFY 발생
--   - FortiManager Push Service가 실시간으로 감지
--
-- Changes:
--   - INSERT/UPDATE/DELETE 시 blacklist_changes 채널로 알림

-- Create trigger function
CREATE OR REPLACE FUNCTION notify_blacklist_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Send notification
    PERFORM pg_notify(
        'blacklist_changes',
        json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'timestamp', NOW()
        )::text
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS blacklist_changes_trigger ON blacklist_ips;

-- Create trigger on blacklist_ips
CREATE TRIGGER blacklist_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON blacklist_ips
FOR EACH STATEMENT
EXECUTE FUNCTION notify_blacklist_changes();

-- Also add trigger for whitelist_ips (optional)
DROP TRIGGER IF EXISTS whitelist_changes_trigger ON whitelist_ips;

CREATE TRIGGER whitelist_changes_trigger
AFTER INSERT OR UPDATE OR DELETE ON whitelist_ips
FOR EACH STATEMENT
EXECUTE FUNCTION notify_blacklist_changes();

COMMENT ON FUNCTION notify_blacklist_changes() IS 'Send NOTIFY on blacklist/whitelist changes for real-time sync';
COMMENT ON TRIGGER blacklist_changes_trigger ON blacklist_ips IS 'Real-time notification for FortiManager Push Service';
COMMENT ON TRIGGER whitelist_changes_trigger ON whitelist_ips IS 'Real-time notification for FortiManager Push Service';
