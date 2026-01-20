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

-- 1. 블랙리스트 IP 테이블 (메인 테이블)
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    reason TEXT,
    source VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT 'unknown',
    confidence_level INTEGER DEFAULT 50 CHECK (confidence_level >= 0 AND confidence_level <= 100),
    detection_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    country VARCHAR(10),                      -- ISO 국가 코드
    detection_date DATE,                      -- 최초 탐지 날짜
    removal_date DATE,                        -- 블랙리스트 제거 날짜
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT unique_ip_source UNIQUE(ip_address, source),
    CONSTRAINT valid_ip_format CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$'),
    CONSTRAINT detection_before_removal CHECK (removal_date IS NULL OR detection_date <= removal_date)
);

-- 2. 수집 인증정보 테이블 (is_active 컬럼 포함)
CREATE TABLE IF NOT EXISTS collection_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(255),
    password TEXT,
    config JSONB DEFAULT '{}',
    encrypted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,           -- 활성 상태 컬럼 추가
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 제약 조건
    CONSTRAINT valid_service_name CHECK (service_name ~ '^[A-Z_]+$')
);

-- 3. 수집 이력 테이블
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
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

-- 4. 모니터링 데이터 테이블
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

-- 5. 시스템 로그 테이블
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

-- 6. 수집 상태 테이블
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

-- 7. 파이프라인 메트릭 테이블
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

-- 8. 수집 메트릭 테이블
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

-- =============================================
-- 인덱스 생성 (성능 최적화)
-- =============================================

-- blacklist_ips 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_ip ON blacklist_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_source ON blacklist_ips(source);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_category ON blacklist_ips(category);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_last_seen ON blacklist_ips(last_seen);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_active ON blacklist_ips(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_confidence ON blacklist_ips(confidence_level);

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
CREATE OR REPLACE VIEW active_blacklist AS
SELECT
    ip_address,
    reason,
    source,
    category,
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
CREATE OR REPLACE VIEW collection_statistics AS
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
CREATE OR REPLACE VIEW recent_activity AS
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

-- REGTECH 인증 정보 기본값 (is_active 포함)
INSERT INTO collection_credentials (service_name, username, password, config, is_active)
VALUES (
    'REGTECH',
    '',
    '',
    '{"base_url": "https://regtech.fsec.or.kr", "timeout": 30, "max_retries": 3}',
    TRUE
)
ON CONFLICT (service_name) DO UPDATE SET
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- 기본 수집 상태 설정
INSERT INTO collection_status (service_name, enabled, status, config) VALUES
('REGTECH', TRUE, 'idle', '{"schedule": "0 */6 * * *", "enabled": true}'),
('THREAT_INTEL', TRUE, 'idle', '{"schedule": "0 */12 * * *", "enabled": false}'),
('MALICIOUS_LIST', TRUE, 'idle', '{"schedule": "0 */24 * * *", "enabled": false}')
ON CONFLICT (service_name) DO NOTHING;

-- =============================================
-- 권한 설정
-- =============================================

-- 모든 테이블과 시퀀스에 대한 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- 읽기 전용 사용자를 위한 권한 (필요시 활성화)
-- CREATE USER blacklist_readonly WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE blacklist TO blacklist_readonly;
-- GRANT USAGE ON SCHEMA public TO blacklist_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO blacklist_readonly;

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
    RAISE NOTICE '✅ 스키마 초기화가 성공적으로 완료되었습니다.';
END $$;