-- REGTECH 수집 데이터를 위한 새 컬럼 추가
-- 2025-09-08 Created

-- 1. detection_date (탐지일) 컬럼 추가
ALTER TABLE blacklist_ips 
ADD COLUMN IF NOT EXISTS detection_date DATE;

-- 2. removal_date (해제일) 컬럼 추가  
ALTER TABLE blacklist_ips 
ADD COLUMN IF NOT EXISTS removal_date DATE;

-- 3. country (국가) 컬럼 추가
ALTER TABLE blacklist_ips 
ADD COLUMN IF NOT EXISTS country VARCHAR(10);

-- 4. 인덱스 추가 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_country ON blacklist_ips(country);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_detection_date ON blacklist_ips(detection_date);
CREATE INDEX IF NOT EXISTS idx_blacklist_ips_removal_date ON blacklist_ips(removal_date);

-- 5. 코멘트 추가 (문서화)
COMMENT ON COLUMN blacklist_ips.detection_date IS 'REGTECH에서 IP가 처음 탐지된 날짜';
COMMENT ON COLUMN blacklist_ips.removal_date IS 'REGTECH에서 IP가 블랙리스트에서 해제될 예정일';
COMMENT ON COLUMN blacklist_ips.country IS 'IP 주소의 국가 코드 (ISO 3166-1 alpha-2)';