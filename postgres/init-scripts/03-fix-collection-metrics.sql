-- 🔧 collection_metrics 테이블 서비스명 컬럼 누락 수정
-- service_name 컬럼이 NOT NULL 제약조건을 위반하는 문제 해결

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'collection_metrics') THEN
        RAISE NOTICE '🔧 collection_metrics 테이블 서비스명 컬럼 누락 문제 수정 시작...';

        -- service_name 컬럼이 NULL을 허용하도록 변경 (기존 데이터 보존)
        IF EXISTS (SELECT FROM information_schema.columns
                  WHERE table_name = 'collection_metrics' AND column_name = 'service_name') THEN
            -- NOT NULL 제약조건 제거
            ALTER TABLE collection_metrics ALTER COLUMN service_name DROP NOT NULL;

            -- 기존 NULL 값들을 기본값으로 업데이트
            UPDATE collection_metrics
            SET service_name = 'regtech'
            WHERE service_name IS NULL;

            RAISE NOTICE '✅ service_name 컬럼 NULL 제약조건 제거 및 기본값 설정 완료';
        END IF;

        -- source_name을 service_name으로 통합 (누락 방지)
        IF EXISTS (SELECT FROM information_schema.columns
                  WHERE table_name = 'collection_metrics' AND column_name = 'source_name') THEN
            -- source_name 값을 service_name에 복사 (service_name이 NULL인 경우)
            UPDATE collection_metrics
            SET service_name = COALESCE(service_name, source_name, 'regtech')
            WHERE service_name IS NULL;

            RAISE NOTICE '✅ source_name 값을 service_name으로 통합 완료';
        END IF;

        -- 향후 삽입 시 기본값 설정
        ALTER TABLE collection_metrics ALTER COLUMN service_name SET DEFAULT 'regtech';

        RAISE NOTICE '🎉 collection_metrics 서비스명 컬럼 문제 수정 완료';
    ELSE
        RAISE NOTICE '❌ collection_metrics 테이블이 존재하지 않습니다.';
    END IF;
END $$;

-- 컬럼 정보 확인
\echo '📋 collection_metrics 테이블 구조:'
\d collection_metrics;