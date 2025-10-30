-- Add missing tables and indexes to bring database schema up to date
-- 2025-09-16: Schema consistency fixes for pipeline_metrics, collection_metrics, and missing indexes

BEGIN;

-- 1. Create pipeline_metrics table (if not exists)
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    execution_time DECIMAL(10,3),
    success_rate DECIMAL(5,2),
    error_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 2. Create collection_metrics table (if not exists)
CREATE TABLE IF NOT EXISTS collection_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    avg_execution_time DECIMAL(10,3),
    last_collection TIMESTAMP,
    metadata JSONB
);

-- 3. Add missing removal_date index to blacklist_ips (if not exists)
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);

-- 4. Add indexes for new tables (if not exists)
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_service ON collection_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_last_collection ON collection_metrics(last_collection);

-- 5. Add comments for documentation
COMMENT ON TABLE pipeline_metrics IS 'CI/CD 파이프라인 성능 메트릭 추적';
COMMENT ON TABLE collection_metrics IS '데이터 수집 서비스 성능 메트릭 추적';

COMMENT ON COLUMN pipeline_metrics.pipeline_name IS '파이프라인 이름 (예: deploy, build, test)';
COMMENT ON COLUMN pipeline_metrics.execution_time IS '실행 시간 (초 단위)';
COMMENT ON COLUMN pipeline_metrics.success_rate IS '성공률 (백분율)';
COMMENT ON COLUMN pipeline_metrics.error_count IS '오류 발생 횟수';
COMMENT ON COLUMN pipeline_metrics.metadata IS '추가 메타데이터 (JSON)';

COMMENT ON COLUMN collection_metrics.service_name IS '수집 서비스 이름 (REGTECH, SECUDIUM 등)';
COMMENT ON COLUMN collection_metrics.collection_count IS '총 수집 횟수';
COMMENT ON COLUMN collection_metrics.success_count IS '성공한 수집 횟수';
COMMENT ON COLUMN collection_metrics.avg_execution_time IS '평균 실행 시간 (초 단위)';
COMMENT ON COLUMN collection_metrics.last_collection IS '마지막 수집 시간';
COMMENT ON COLUMN collection_metrics.metadata IS '추가 메타데이터 (JSON)';

COMMIT;

-- 결과 확인
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserted_rows,
    n_tup_upd as updated_rows,
    n_tup_del as deleted_rows
FROM pg_stat_user_tables
WHERE tablename IN ('blacklist_ips', 'collection_history', 'monitoring_data', 'pipeline_metrics', 'collection_metrics', 'collection_credentials')
ORDER BY tablename;

-- 인덱스 확인
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('blacklist_ips', 'pipeline_metrics', 'collection_metrics')
ORDER BY tablename, indexname;