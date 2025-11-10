# Blacklist Service - 데모 가이드

## 빠른 시작 (Quick Start)

### 1. 환경 준비
```bash
cd /home/jclee/app/blacklist

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 REGTECH_ID, REGTECH_PW 설정

# 서비스 시작
docker-compose up -d
```

### 2. Health Check
```bash
# 서비스 상태 확인
curl http://blacklist.jclee.me:2542/health

# 예상 응답
{
  "status": "healthy",
  "services": {
    "postgres": "ok",
    "redis": "ok",
    "collector": "ok"
  }
}
```

### 3. API 사용 예제

#### 블랙리스트 조회
```bash
# 전체 목록 조회
curl https://blacklist.jclee.me/api/v1/blacklist

# 특정 이름 검색
curl https://blacklist.jclee.me/api/v1/blacklist?name=홍길동

# 주민번호로 검색
curl https://blacklist.jclee.me/api/v1/blacklist?ssn=123456-1234567
```

#### 통계 조회
```bash
# 전체 통계
curl https://blacklist.jclee.me/api/v1/stats

# 예상 응답
{
  "total_records": 15432,
  "last_updated": "2025-10-11T17:00:00Z",
  "categories": {
    "금융사기": 8234,
    "다단계": 3421,
    "보이스피싱": 3777
  }
}
```

## 데모 시나리오

### 시나리오 1: 실시간 블랙리스트 확인
```bash
# 1. 데이터 수집 (manual trigger)
curl -X POST https://blacklist.jclee.me/api/v1/collect

# 2. 최신 데이터 조회
curl https://blacklist.jclee.me/api/v1/blacklist?limit=10&sort=latest

# 3. Grafana에서 수집 로그 확인
# grafana.jclee.me → Loki → {job="blacklist"}
```

### 시나리오 2: 캐시 성능 테스트
```bash
# 첫 번째 요청 (DB 조회)
time curl https://blacklist.jclee.me/api/v1/blacklist?name=홍길동
# 응답 시간: ~200ms

# 두 번째 요청 (Redis 캐시)
time curl https://blacklist.jclee.me/api/v1/blacklist?name=홍길동
# 응답 시간: ~20ms (10배 개선)
```

### 시나리오 3: 모니터링 통합
```bash
# Prometheus 메트릭 확인
curl https://blacklist.jclee.me:2542/metrics

# Grafana 대시보드
# grafana.jclee.me → Dashboards → Blacklist Service
# - HTTP 요청 수
# - 응답 시간 (P50, P95, P99)
# - 에러율
# - 캐시 히트율
```

## Troubleshooting

### 문제 1: 서비스 응답 없음
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs blacklist-app

# Grafana Loki에서 에러 로그 검색
# {job="blacklist"} |~ "error|ERROR"
```

### 문제 2: RegTech API 연동 실패
```bash
# Collector 로그 확인
docker-compose logs blacklist-collector

# 자격 증명 확인
echo $REGTECH_ID
echo $REGTECH_PW

# 수동 재시작
docker-compose restart blacklist-collector
```

### 문제 3: 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker-compose exec blacklist-postgres pg_isready

# 연결 테스트
docker-compose exec blacklist-postgres psql -U postgres -d blacklist -c "SELECT COUNT(*) FROM blacklist;"
```

## 고급 사용법

### API 인증 (추후 구현)
```bash
# JWT 토큰 발급
curl -X POST https://blacklist.jclee.me/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 인증된 요청
curl https://blacklist.jclee.me/api/v1/admin/stats \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 배치 작업
```bash
# 자동 수집 활성화 (cron)
# DISABLE_AUTO_COLLECTION=false로 설정
docker-compose up -d

# 수집 스케줄: 매일 02:00 KST
```

## 관련 링크
- [API 문서](../docs/api.md)
- [아키텍처 설계](../docs/architecture.md)
- [프로젝트 이력서](../resume/README.md)
- [Grafana 대시보드](https://grafana.jclee.me)
