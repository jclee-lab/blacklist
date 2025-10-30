-- 통합 IP 관리 뷰 생성
-- 블랙리스트와 화이트리스트를 하나의 뷰로 통합

-- 1. 통합 IP 뷰 (blacklist + whitelist)
CREATE OR REPLACE VIEW unified_ip_list AS
SELECT
    'blacklist' as list_type,
    id,
    ip_address,
    reason,
    source,
    confidence_level,
    detection_count,
    is_active,
    country,
    detection_date,
    removal_date,
    last_seen,
    created_at,
    updated_at,
    raw_data
FROM blacklist_ips
UNION ALL
SELECT
    'whitelist' as list_type,
    id,
    ip_address,
    reason,
    source,
    NULL as confidence_level,
    NULL as detection_count,
    TRUE as is_active,  -- 화이트리스트는 항상 활성
    country,
    NULL as detection_date,
    NULL as removal_date,
    NULL as last_seen,
    created_at,
    updated_at,
    NULL as raw_data
FROM whitelist_ips;

-- 2. 활성 IP 통합 뷰 (해제일 체크 포함)
CREATE OR REPLACE VIEW active_unified_ip_list AS
SELECT
    list_type,
    ip_address,
    reason,
    source,
    country,
    detection_date,
    removal_date,
    created_at,
    CASE
        WHEN list_type = 'whitelist' THEN TRUE
        WHEN list_type = 'blacklist' AND (removal_date IS NULL OR removal_date > CURRENT_DATE) THEN TRUE
        ELSE FALSE
    END as is_active
FROM unified_ip_list
WHERE
    (list_type = 'whitelist')
    OR
    (list_type = 'blacklist' AND is_active = TRUE AND (removal_date IS NULL OR removal_date > CURRENT_DATE));

-- 3. IP 우선순위 체크 뷰 (화이트리스트 우선)
CREATE OR REPLACE VIEW ip_priority_check AS
WITH ip_list AS (
    SELECT DISTINCT ip_address FROM unified_ip_list
)
SELECT
    il.ip_address,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM whitelist_ips w WHERE w.ip_address = il.ip_address
        ) THEN 'whitelist'
        WHEN EXISTS (
            SELECT 1 FROM blacklist_ips_with_auto_inactive b
            WHERE b.ip_address = il.ip_address AND b.is_active = TRUE
        ) THEN 'blacklist'
        ELSE 'unknown'
    END as priority_type,
    (SELECT reason FROM whitelist_ips WHERE ip_address = il.ip_address LIMIT 1) as whitelist_reason,
    (SELECT reason FROM blacklist_ips_with_auto_inactive WHERE ip_address = il.ip_address AND is_active = TRUE LIMIT 1) as blacklist_reason,
    (SELECT country FROM whitelist_ips WHERE ip_address = il.ip_address LIMIT 1) as country
FROM ip_list il;

-- 4. 통합 통계 뷰
CREATE OR REPLACE VIEW unified_ip_statistics AS
SELECT
    list_type,
    source,
    country,
    COUNT(*) as total_count,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_count,
    COUNT(CASE WHEN is_active = FALSE THEN 1 END) as inactive_count,
    MIN(created_at) as first_added,
    MAX(created_at) as last_added
FROM unified_ip_list
GROUP BY list_type, source, country
ORDER BY list_type, source, country;

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_active
ON blacklist_ips(removal_date, is_active)
WHERE removal_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_blacklist_ips_list_type
ON blacklist_ips(source, is_active);

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '✅ 통합 IP 뷰 생성 완료';
    RAISE NOTICE '   - unified_ip_list: 전체 IP 통합 뷰';
    RAISE NOTICE '   - active_unified_ip_list: 활성 IP만 (해제일 체크)';
    RAISE NOTICE '   - ip_priority_check: IP 우선순위 체크 (화이트리스트 우선)';
    RAISE NOTICE '   - unified_ip_statistics: 통합 통계';
END $$;
