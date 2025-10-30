-- SECUDIUM 가짜 데이터 정리 마이그레이션
-- 2025-09-03: SECUDIUM 서비스 제거로 인한 데이터 정리

BEGIN;

-- 1. SECUDIUM 소스 데이터 삭제
DELETE FROM blacklist_ips 
WHERE source LIKE '%secudium%' 
   OR source LIKE '%SECUDIUM%'
   OR source LIKE 'SECUDIUM_%';

-- 2. SECUDIUM 수집 통계 삭제
DELETE FROM collection_stats 
WHERE source = 'secudium' 
   OR source = 'SECUDIUM';

-- 3. SECUDIUM 수집 기록 삭제
DELETE FROM collection_history 
WHERE source_name LIKE '%secudium%' 
   OR source_name LIKE '%SECUDIUM%';

-- 4. SECUDIUM 인증 정보 삭제
DELETE FROM collection_credentials 
WHERE service_name = 'SECUDIUM' 
   OR service_name = 'secudium';

-- 5. 통계 정보 갱신
VACUUM ANALYZE blacklist_ips;
VACUUM ANALYZE collection_stats;
VACUUM ANALYZE collection_history;

COMMIT;

-- 결과 확인
SELECT 'Cleanup Complete' as status, 
       COUNT(*) as remaining_ips,
       string_agg(DISTINCT source, ', ') as remaining_sources
FROM blacklist_ips;