-- 전체 데이터베이스 초기화 스크립트
-- 2025-09-03: 깨끗한 상태에서 시작하기 위한 완전 초기화

BEGIN;

-- 1. 모든 IP 데이터 삭제
DELETE FROM blacklist_ips;

-- 2. 모든 수집 통계 삭제
DELETE FROM collection_stats;

-- 3. 모든 수집 기록 삭제
DELETE FROM collection_history;

-- 4. 시퀀스 리셋 (ID가 1부터 다시 시작)
ALTER SEQUENCE blacklist_ips_id_seq RESTART WITH 1;

-- 5. 테이블 최적화
VACUUM ANALYZE blacklist_ips;
VACUUM ANALYZE collection_stats;
VACUUM ANALYZE collection_history;

COMMIT;

-- 결과 확인
SELECT 'Database Reset Complete' as status, 
       COUNT(*) as remaining_ips
FROM blacklist_ips;

-- 테이블 상태 확인
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserted_rows,
    n_tup_upd as updated_rows,
    n_tup_del as deleted_rows
FROM pg_stat_user_tables 
WHERE tablename IN ('blacklist_ips', 'collection_stats', 'collection_history');