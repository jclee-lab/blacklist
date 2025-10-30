-- 🔄 pipeline_metrics 테이블 안전한 마이그레이션
-- 기존 데이터를 유지하면서 테이블 구조 업데이트

-- 테이블이 존재하는지 확인
DO $$
BEGIN
    -- pipeline_metrics 테이블이 존재하지만 올바른 구조가 아닌 경우 마이그레이션 수행
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'pipeline_metrics') THEN
        -- 현재 테이블 구조 확인
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'pipeline_metrics'
                      AND column_name = 'status'
                      AND data_type = 'character varying') THEN

            RAISE NOTICE '🔄 pipeline_metrics 테이블 마이그레이션 시작...';

            -- 1. 기존 데이터 백업
            DROP TABLE IF EXISTS pipeline_metrics_backup;
            CREATE TABLE pipeline_metrics_backup AS SELECT * FROM pipeline_metrics;

            RAISE NOTICE '📁 기존 데이터 백업 완료: % 레코드', (SELECT COUNT(*) FROM pipeline_metrics_backup);

            -- 2. 기존 테이블 삭제
            DROP TABLE pipeline_metrics CASCADE;

            -- 3. 새로운 구조로 테이블 재생성
            CREATE TABLE pipeline_metrics (
                timestamp TIMESTAMP NOT NULL,
                pipeline_name VARCHAR(100) NOT NULL,
                execution_time DECIMAL(10,3),
                success_rate DECIMAL(5,2),
                error_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'unknown',
                metadata JSONB,
                PRIMARY KEY (timestamp, pipeline_name)
            );

            RAISE NOTICE '🏗️ 새로운 테이블 구조 생성 완료';

            -- 4. 백업 데이터에서 복원 (호환 가능한 컬럼만)
            INSERT INTO pipeline_metrics (timestamp, pipeline_name, execution_time, success_rate, error_count, status, metadata)
            SELECT
                COALESCE(timestamp, NOW()) as timestamp,
                COALESCE(pipeline_name, 'unknown') as pipeline_name,
                execution_time,
                COALESCE(success_rate, 0) as success_rate,
                COALESCE(error_count, 0) as error_count,
                COALESCE(status, 'unknown') as status,
                metadata
            FROM pipeline_metrics_backup
            ON CONFLICT (timestamp, pipeline_name) DO NOTHING;

            RAISE NOTICE '📊 데이터 복원 완료: % 레코드', (SELECT COUNT(*) FROM pipeline_metrics);

            -- 5. 백업 테이블 정리
            DROP TABLE pipeline_metrics_backup;

            RAISE NOTICE '✅ pipeline_metrics 테이블 마이그레이션 완료';

        ELSE
            RAISE NOTICE '✅ pipeline_metrics 테이블이 이미 올바른 구조입니다.';
        END IF;
    ELSE
        RAISE NOTICE '❌ pipeline_metrics 테이블이 존재하지 않습니다. 01-init-database.sql에서 생성됩니다.';
    END IF;
END $$;

-- collection_metrics 테이블 완전한 구조 수정
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'collection_metrics') THEN
        RAISE NOTICE '🔄 collection_metrics 테이블 구조 확인 및 수정...';

        -- 누락된 컬럼들 추가
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'timestamp') THEN
            ALTER TABLE collection_metrics ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE '✅ timestamp 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'source_name') THEN
            ALTER TABLE collection_metrics ADD COLUMN source_name VARCHAR(100);
            RAISE NOTICE '✅ source_name 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'items_collected') THEN
            ALTER TABLE collection_metrics ADD COLUMN items_collected INTEGER DEFAULT 0;
            RAISE NOTICE '✅ items_collected 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'success') THEN
            ALTER TABLE collection_metrics ADD COLUMN success BOOLEAN DEFAULT FALSE;
            RAISE NOTICE '✅ success 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'execution_time_ms') THEN
            ALTER TABLE collection_metrics ADD COLUMN execution_time_ms INTEGER DEFAULT 0;
            RAISE NOTICE '✅ execution_time_ms 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'error_message') THEN
            ALTER TABLE collection_metrics ADD COLUMN error_message TEXT;
            RAISE NOTICE '✅ error_message 컬럼 추가';
        END IF;

        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name = 'collection_metrics' AND column_name = 'memory_usage_mb') THEN
            ALTER TABLE collection_metrics ADD COLUMN memory_usage_mb DECIMAL(10,4);
            RAISE NOTICE '✅ memory_usage_mb 컬럼 추가';
        END IF;

        -- PRIMARY KEY 또는 UNIQUE 제약조건 추가 (ON CONFLICT 지원을 위해)
        IF NOT EXISTS (SELECT FROM information_schema.table_constraints
                      WHERE table_name = 'collection_metrics'
                      AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                      AND constraint_name LIKE '%timestamp%source_name%') THEN

            -- 기존 중복 데이터 정리
            DELETE FROM collection_metrics a USING collection_metrics b
            WHERE a.id > b.id
            AND a.timestamp = b.timestamp
            AND a.source_name = b.source_name;

            -- UNIQUE 제약조건 추가
            ALTER TABLE collection_metrics
            ADD CONSTRAINT uk_collection_metrics_timestamp_source
            UNIQUE (timestamp, source_name);

            RAISE NOTICE '✅ collection_metrics UNIQUE 제약조건 추가';
        END IF;

        RAISE NOTICE '✅ collection_metrics 테이블 구조 업데이트 완료';
    END IF;
END $$;

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name ON pipeline_metrics(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_timestamp ON pipeline_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status ON pipeline_metrics(status);

-- collection_metrics 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_metrics_timestamp ON collection_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_source_name ON collection_metrics(source_name);
CREATE INDEX IF NOT EXISTS idx_collection_metrics_success ON collection_metrics(success);

DO $$
BEGIN
    RAISE NOTICE '🎉 모든 데이터베이스 마이그레이션이 완료되었습니다.';
END $$;