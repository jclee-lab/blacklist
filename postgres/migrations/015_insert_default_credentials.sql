-- 015_insert_default_credentials.sql
-- 기본 REGTECH/SECUDIUM credentials 생성 (placeholder)
-- 재부팅 시에도 안전 (이미 있으면 무시)

-- REGTECH 기본 credentials (비활성화 상태)
INSERT INTO collection_credentials (
    service_name,
    username,
    password,
    config,
    is_active,
    enabled,
    collected_count
)
VALUES (
    'REGTECH',
    'PLEASE_SET',  -- 사용자가 변경 필요
    pgp_sym_encrypt('PLEASE_SET', 'blacklist-secret-key-2024'),
    '{
        "base_url": "https://regtech.fsec.or.kr",
        "timeout": 30,
        "max_retries": 3
    }'::jsonb,
    false,  -- 비활성화 (사용자가 활성화 필요)
    false,  -- 비활성화
    0
)
ON CONFLICT (service_name) DO NOTHING;  -- 이미 있으면 무시

-- SECUDIUM 기본 credentials (비활성화 상태)
INSERT INTO collection_credentials (
    service_name,
    username,
    password,
    config,
    is_active,
    enabled,
    collected_count
)
VALUES (
    'SECUDIUM',
    'PLEASE_SET',  -- 사용자가 변경 필요
    pgp_sym_encrypt('PLEASE_SET', 'blacklist-secret-key-2024'),
    '{
        "base_url": "https://www.secudium.com",
        "timeout": 30,
        "max_retries": 3
    }'::jsonb,
    false,  -- 비활성화 (사용자가 활성화 필요)
    false,  -- 비활성화
    0
)
ON CONFLICT (service_name) DO NOTHING;  -- 이미 있으면 무시

-- 메시지 출력
DO $$
BEGIN
    RAISE NOTICE '✅ Default credentials initialized (PLEASE_SET placeholders)';
    RAISE NOTICE '   Update credentials via collection panel UI';
END $$;
