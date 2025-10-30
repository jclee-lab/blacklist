-- 🗄️ Blacklist Management System - Complete Database Schema
-- REGTECH Blacklist Intelligence Platform
-- Version: 3.0.0 (September 2025)
-- 모든 스키마를 이미지에 정의하여 완전한 일관성 보장

-- =============================================
-- 데이터베이스 초기화
-- =============================================

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE blacklist'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'blacklist')\gexec

-- Connect to blacklist database
\c blacklist;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 텍스트 검색 최적화

-- =============================================
-- 핵심 테이블 정의
-- =============================================

-- 1. 블랙리스트 IP 테이블 (메인 테이블) - raw_data 필드 추가
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,                              -- 탐지 사유/내용 (예: 웹 애플리케이션 공격 탐지, SQL Injection 공격 등)
    source VARCHAR(100) NOT NULL,
    confidence_level INTEGER DEFAULT 50 CHECK (confidence_level >= 0 AND confidence_level <= 100),
    detection_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    country VARCHAR(10),                      -- ISO 국가 코드
    detection_date DATE,                      -- 최초 탐지 날짜
    removal_date DATE,                        -- 블랙리스트 제거 날짜
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB DEFAULT '{}',              -- 원본 수집 데이터 (배열 형태: [IP, 국가, 탐지내용, 탐지일, 해제일, ...])

    -- 제약 조건
    CONSTRAINT unique_ip_source UNIQUE(ip_address, source),
    CONSTRAINT valid_ip_format CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$'),
    CONSTRAINT detection_before_removal CHECK (removal_date IS NULL OR detection_date <= removal_date)
);

-- 2. 화이트리스트 IP 테이블 (우선순위 최상위)
CREATE TABLE IF NOT EXISTS whitelist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,                              -- 화이트리스트 등록 사유
    source VARCHAR(100) NOT NULL,
    country VARCHAR(10),                      -- ISO 국가 코드
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT unique_whitelist_ip_source UNIQUE(ip_address, source),
    CONSTRAINT valid_whitelist_ip_format CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$')
);

-- 3. 수집 인증정보 테이블 (완전한 수집 관리 컬럼 포함)
CREATE TABLE IF NOT EXISTS collection_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(255),
    password TEXT,
    config JSONB DEFAULT '{}',
    encrypted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,           -- 활성 상태 컬럼
    enabled BOOLEAN DEFAULT TRUE,             -- 수집 활성화 여부
    collection_interval INTEGER DEFAULT 3600, -- 수집 주기 (초)
    last_collection TIMESTAMP,                -- 마지막 수집 시간
    last_success BOOLEAN,                     -- 마지막 수집 성공 여부
    collected_count INTEGER DEFAULT 0,        -- 총 수집 횟수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT valid_service_name CHECK (service_name ~ '^[A-Z_]+$'),
    CONSTRAINT positive_collection_interval CHECK (collection_interval > 0),
    CONSTRAINT non_negative_collected_count CHECK (collected_count >= 0)
);

-- 4. 수집 이력 테이블
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_type VARCHAR(50) DEFAULT 'manual',  -- 'manual' or 'automatic'
    collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items_collected INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    details JSONB DEFAULT '{}',

    -- 제약 조건
    CONSTRAINT positive_items CHECK (items_collected >= 0),
    CONSTRAINT positive_execution_time CHECK (execution_time_ms >= 0)
);

-- 5. 모니터링 데이터 테이블
CREATE TABLE IF NOT EXISTS monitoring_data (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}',
    numeric_value DECIMAL(12,4),             -- 호환성을 위한 중복 컬럼
    unit VARCHAR(20),                        -- 호환성을 위한 중복 컬럼

    -- 제약 조건
    CONSTRAINT valid_metric_name CHECK (metric_name != '')
);

-- 6. 시스템 로그 테이블
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_context JSONB DEFAULT '{}',

    -- 제약 조건
    CONSTRAINT valid_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- 7. 수집 상태 테이블
CREATE TABLE IF NOT EXISTS collection_status (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    status VARCHAR(50) DEFAULT 'idle',
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT valid_status CHECK (status IN ('idle', 'running', 'error', 'disabled')),
    CONSTRAINT non_negative_counts CHECK (error_count >= 0 AND success_count >= 0)
);

-- 8. 파이프라인 메트릭 테이블
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    timestamp TIMESTAMP NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    execution_time DECIMAL(10,3) DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'unknown',
    metadata JSONB DEFAULT '{}',

    -- 제약 조건
    PRIMARY KEY (timestamp, pipeline_name),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT non_negative_error_count CHECK (error_count >= 0)
);

-- 9. 수집 메트릭 테이블
CREATE TABLE IF NOT EXISTS collection_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    collection_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    avg_execution_time DECIMAL(10,3) DEFAULT 0,
    last_collection TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT non_negative_metrics CHECK (
        collection_count >= 0 AND
        success_count >= 0 AND
        avg_execution_time >= 0
    ),
    CONSTRAINT success_not_exceed_total CHECK (success_count <= collection_count)
);

-- 10. 수집 통계 테이블 (collection_stats)
CREATE TABLE IF NOT EXISTS collection_stats (
    source VARCHAR(100) PRIMARY KEY,
    total_ips INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,

    -- 제약 조건
    CONSTRAINT non_negative_total_ips CHECK (total_ips >= 0)
);

-- =============================================
-- 인덱스 생성 (성능 최적화)
-- =============================================

-- blacklist_ips 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_ip ON blacklist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
-- CREATE INDEX IF NOT EXISTS idx_blacklist_ips_category ON blacklist_ips(category); -- category column does not exist
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_last_seen ON blacklist_ips(last_seen);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_confidence ON blacklist_ips(confidence_level);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_raw_data ON blacklist_ips USING GIN (raw_data);  -- JSONB 전체 텍스트 검색

-- whitelist_ips 테이블 인덱스 (우선순위 체크용)
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_ip ON whitelist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_source ON whitelist_ips(source);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_country ON whitelist_ips(country);
CREATE INDEX IF NOT EXISTS idx_whitelist_ips_created_at ON whitelist_ips(created_at);

-- collection_credentials 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_credentials_service ON collection_credentials(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_credentials_active ON collection_credentials(service_name, is_active);

-- collection_history 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_history_service ON collection_history(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_history_date ON collection_history(collection_date);
CREATE INDEX IF NOT EXISTS idx_collection_history_success ON collection_history(success);

-- monitoring_data 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_monitoring_data_metric ON monitoring_data(metric_name);
CREATE INDEX IF NOT EXISTS idx_monitoring_data_timestamp ON monitoring_data(timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_monitoring_unique ON monitoring_data (metric_name, timestamp);

-- system_logs 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);

-- collection_status 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_status_service ON collection_status(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_status_enabled ON collection_status(enabled);
CREATE INDEX IF NOT EXISTS idx_collection_status_last_run ON collection_status(last_run);

-- pipeline_metrics 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status ON pipeline_metrics(status);

-- collection_metrics 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_metrics_service ON collection_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_last_collection ON collection_metrics(last_collection);

-- =============================================
-- 뷰 생성 (조회 최적화)
-- =============================================

-- 활성 블랙리스트 뷰
DROP VIEW IF EXISTS active_blacklist CASCADE;
CREATE VIEW active_blacklist AS
SELECT
    ip_address,
    reason,
    source,
    --     category,
    confidence_level,
    country,
    detection_date,
    detection_count,
    last_seen,
    created_at
FROM blacklist_ips
WHERE is_active = TRUE
ORDER BY last_seen DESC, confidence_level DESC;

-- 수집 통계 뷰
DROP VIEW IF EXISTS collection_statistics CASCADE;
CREATE VIEW collection_statistics AS
SELECT
    service_name,
    COUNT(*) as total_collections,
    COUNT(CASE WHEN success = true THEN 1 END) as successful_collections,
    ROUND(
        COUNT(CASE WHEN success = true THEN 1 END)::decimal /
        COUNT(*)::decimal * 100, 2
    ) as success_rate,
    SUM(items_collected) as total_items_collected,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(collection_date) as last_collection_date
FROM collection_history
GROUP BY service_name
ORDER BY total_collections DESC;

-- 최근 활동 뷰
DROP VIEW IF EXISTS recent_activity CASCADE;
CREATE VIEW recent_activity AS
SELECT
    'collection' as activity_type,
    service_name as source,
    items_collected as count,
    collection_date as timestamp,
    success as status
FROM collection_history
WHERE collection_date >= NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    'blacklist_update' as activity_type,
    source,
    1 as count,
    updated_at as timestamp,
    true as status
FROM blacklist_ips
WHERE updated_at >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- =============================================
-- 트리거 함수 생성 (자동화)
-- =============================================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- blacklist_ips 테이블의 updated_at 트리거
DROP TRIGGER IF EXISTS update_blacklist_ips_updated_at ON blacklist_ips;
CREATE TRIGGER update_blacklist_ips_updated_at
    BEFORE UPDATE ON blacklist_ips
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- collection_credentials 테이블의 updated_at 트리거
DROP TRIGGER IF EXISTS update_collection_credentials_updated_at ON collection_credentials;
CREATE TRIGGER update_collection_credentials_updated_at
    BEFORE UPDATE ON collection_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- collection_status 테이블의 updated_at 트리거
DROP TRIGGER IF EXISTS update_collection_status_updated_at ON collection_status;
CREATE TRIGGER update_collection_status_updated_at
    BEFORE UPDATE ON collection_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- collection_metrics 테이블의 updated_at 트리거
DROP TRIGGER IF EXISTS update_collection_metrics_updated_at ON collection_metrics;
CREATE TRIGGER update_collection_metrics_updated_at
    BEFORE UPDATE ON collection_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- 기본 데이터 삽입
-- =============================================

-- REGTECH 인증 정보 기본값 (전체 컬럼 포함)
INSERT INTO collection_credentials (service_name, username, password, config, is_active, enabled, collection_interval)
VALUES (
    'REGTECH',
    '',
    '',
    '{"base_url": "https://regtech.fsec.or.kr", "timeout": 30, "max_retries": 3}',
    TRUE,
    FALSE,  -- 기본적으로 비활성 (수동 수집만)
    21600   -- 6시간 (6 * 3600)
)
ON CONFLICT (service_name) DO UPDATE SET
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active,
    enabled = EXCLUDED.enabled,
    collection_interval = EXCLUDED.collection_interval,
    updated_at = NOW();

-- 기본 수집 상태 설정 (자동수집 기본값 OFF)
INSERT INTO collection_status (service_name, enabled, status, config) VALUES
('REGTECH', FALSE, 'idle', '{"schedule": "0 */6 * * *", "enabled": false}'),
('THREAT_INTEL', FALSE, 'idle', '{"schedule": "0 */12 * * *", "enabled": false}'),
('MALICIOUS_LIST', FALSE, 'idle', '{"schedule": "0 */24 * * *", "enabled": false}')
ON CONFLICT (service_name) DO NOTHING;

-- =============================================
-- 권한 설정
-- =============================================

-- 모든 테이블과 시퀀스에 대한 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- =============================================
-- 자동 비활성 처리 뷰 및 트리거
-- =============================================

-- 해제일 지난 IP 자동 비활성 처리를 위한 뷰
CREATE OR REPLACE VIEW blacklist_ips_with_auto_inactive AS
SELECT
    id,
    ip_address,
    reason,
    source,
    --     category,
    confidence_level,
    detection_count,
    -- 해제일이 지났으면 자동으로 비활성으로 표시
    CASE
        WHEN removal_date IS NOT NULL AND removal_date <= CURRENT_DATE
        THEN false
        ELSE is_active
    END as is_active,
    country,
    detection_date,
    removal_date,
    last_seen,
    created_at,
    updated_at
FROM blacklist_ips;

-- Fortinet API용 활성 IP만 조회하는 뷰
CREATE OR REPLACE VIEW fortinet_active_ips AS
SELECT
    ip_address,
    source,
    --     category,
    confidence_level,
    detection_date,
    removal_date,
    created_at,
    last_seen
FROM blacklist_ips_with_auto_inactive
WHERE is_active = true;

-- 실제 DB 업데이트를 위한 트리거 함수 (선택적)
CREATE OR REPLACE FUNCTION auto_deactivate_expired_ips()
RETURNS TRIGGER AS $$
BEGIN
    -- 매일 자정에 해제일 지난 IP들을 실제로 비활성화
    IF TG_OP = 'UPDATE' AND OLD.updated_at::date < NEW.updated_at::date THEN
        UPDATE blacklist_ips
        SET is_active = false, updated_at = NOW()
        WHERE removal_date IS NOT NULL
        AND removal_date <= CURRENT_DATE
        AND is_active = true;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 블랙리스트 통계 뷰 (자동 비활성 반영)
CREATE OR REPLACE VIEW blacklist_statistics AS
SELECT
    source,
    COUNT(*) as total_ips,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_ips,
    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_ips,
    COUNT(CASE WHEN removal_date IS NOT NULL AND removal_date <= CURRENT_DATE THEN 1 END) as expired_ips,
    MAX(created_at) as last_collection,
    MIN(detection_date) as first_detection,
    MAX(detection_date) as latest_detection
FROM blacklist_ips_with_auto_inactive
GROUP BY source
ORDER BY total_ips DESC;

-- 통합 IP 리스트 뷰 (화이트리스트 + 블랙리스트)
CREATE OR REPLACE VIEW unified_ip_list AS
SELECT
    'whitelist' AS list_type,
    id,
    ip_address,
    reason,
    source,
    NULL::integer AS confidence_level,
    NULL::integer AS detection_count,
    TRUE AS is_active,
    country,
    NULL::date AS detection_date,
    NULL::date AS removal_date,
    NULL::timestamp AS last_seen,
    created_at,
    updated_at
FROM whitelist_ips
UNION ALL
SELECT
    'blacklist' AS list_type,
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
    updated_at
FROM blacklist_ips;

-- =============================================
-- 완료 메시지
-- =============================================

-- 스키마 생성 완료 확인
DO $$
BEGIN
    RAISE NOTICE '🎉 Blacklist Database Schema v3.0.0 완료';
    RAISE NOTICE '📊 테이블: % 개', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE '🔍 인덱스: % 개', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE '👁️ 뷰: % 개', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public');
    RAISE NOTICE '⚡ 트리거: % 개', (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public');
    RAISE NOTICE '🔄 자동 비활성 처리 뷰 생성 완료';
    RAISE NOTICE '✅ 스키마 초기화가 성공적으로 완료되었습니다.';
END $$;