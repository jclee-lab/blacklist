-- Collection Credentials with proper data (전체 컬럼 포함)
-- enabled = false: 스케줄러는 돌지만 자동 수집은 하지 않음 (수동 트리거만)
INSERT INTO collection_credentials (service_name, username, password, is_active, enabled, collection_interval, config) VALUES
('SECUDIUM', 'nextrade', 'Ntmxmec17!', true, false, 3600, '{"timeout": 30, "base_url": "https://secudium.skinfosec.co.kr"}'),
('REGTECH', 'nextrade', 'Sprtmxm1@3', true, false, 21600, '{"timeout": 30, "base_url": "https://regtech.fsec.or.kr", "max_retries": 3}')
ON CONFLICT (service_name) DO UPDATE SET
    username = EXCLUDED.username,
    password = EXCLUDED.password,
    is_active = EXCLUDED.is_active,
    enabled = EXCLUDED.enabled,
    collection_interval = EXCLUDED.collection_interval,
    config = EXCLUDED.config,
    updated_at = NOW();
