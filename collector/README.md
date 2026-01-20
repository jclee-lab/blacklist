# Blacklist Collector

독립적인 블랙리스트 IP 수집 컨테이너

## 개요

`blacklist-collector`는 REGTECH 및 기타 소스에서 블랙리스트 IP를 자동으로 수집하는 독립적인 서비스입니다. 메인 애플리케이션과 분리되어 있어 수집 작업이 웹 서비스에 영향을 주지 않습니다.

## 주요 기능

- **자동 스케줄링**: 설정 가능한 간격으로 자동 수집
- **REGTECH 통합**: 한국금융보안원(REGTECH) 포털 연동
- **데이터베이스 통합**: PostgreSQL에 직접 저장
- **헬스체크**: 모니터링을 위한 REST API 제공
- **독립 실행**: 다른 서비스에 의존하지 않음

## 서비스 구조

```
collector/
├── run_collector.py     # 메인 실행 스크립트 (Entry Point)
├── config.py            # 환경 설정
├── scheduler.py         # 스케줄링 관리
├── scheduler_api.py     # 스케줄러 API
├── health_server.py     # 헬스체크 서버
├── core/                # 핵심 로직
│   ├── database.py      # 데이터베이스 서비스
│   └── regtech_collector.py # REGTECH 수집기
├── api/                 # API 모듈
├── utils/               # 유틸리티
├── Dockerfile           # 컨테이너 빌드
└── requirements.txt     # Python 의존성
```

> **Note:** 이 서비스가 권한있는 ETL 구현입니다.
> `app/core/collectors/`는 폐기 예정이며 사용하지 마세요.

## 환경 변수

### 필수 설정
```bash
# 데이터베이스
POSTGRES_HOST=blacklist-postgres
POSTGRES_PORT=5432
POSTGRES_DB=blacklist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# REGTECH 인증
REGTECH_ID=your_regtech_id
REGTECH_PW=your_regtech_password
REGTECH_BASE_URL=https://regtech.fsec.or.kr
```

### 선택적 설정
```bash
# 수집 설정
COLLECTION_INTERVAL=3600    # 수집 간격 (초)
BATCH_SIZE=1000             # 배치 처리 크기
MAX_RETRY_ATTEMPTS=3        # 재시도 횟수

# 헬스체크
HEALTH_CHECK_PORT=8545      # 헬스체크 포트

# 로그 설정
LOG_LEVEL=INFO              # 로그 레벨
```

## API 엔드포인트

### 헬스체크
```bash
GET /health
```
서비스 상태 확인

### 상세 상태
```bash
GET /status
```
상세한 서비스 정보 및 통계

### 수동 트리거
```bash
POST /trigger
```
수동으로 수집 작업 시작

### 메트릭
```bash
GET /metrics
```
Prometheus 형식의 메트릭

### 설정 조회
```bash
GET /config
```
현재 설정 정보

## Docker 실행

### 단독 실행
```bash
docker run -d \
  --name blacklist-collector \
  --network blacklist-network \
  -e POSTGRES_HOST=blacklist-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e REGTECH_ID=your_id \
  -e REGTECH_PW=your_password \
  -p 8545:8545 \
  ${REGISTRY_DOMAIN:-registry.example.com}/blacklist-collector:latest
```

### Docker Compose
```yaml
blacklist-collector:
  image: ${REGISTRY_DOMAIN:-registry.example.com}/blacklist-collector:latest
  container_name: blacklist-collector
  environment:
    POSTGRES_HOST: blacklist-postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    REGTECH_ID: ${REGTECH_ID}
    REGTECH_PW: ${REGTECH_PW}
    COLLECTION_INTERVAL: 3600
  ports:
    - "8545:8545"
  depends_on:
    - blacklist-postgres
    - blacklist-redis
  restart: unless-stopped
```

## 모니터링

### 상태 확인
```bash
curl http://localhost:8545/health
```

### 수집 통계
```bash
curl http://localhost:8545/status | jq
```

### 로그 확인
```bash
docker logs blacklist-collector --tail 100
```

## 데이터 흐름

1. **스케줄러**: 설정된 간격으로 수집 작업 시작
2. **인증**: REGTECH 포털에 로그인
3. **데이터 수집**: API를 통해 블랙리스트 IP 데이터 조회
4. **데이터 처리**: 중복 제거 및 형식 변환
5. **데이터베이스 저장**: PostgreSQL에 배치 저장
6. **히스토리 기록**: 수집 결과 기록

## 트러블슈팅

### 일반적인 문제

#### 1. 데이터베이스 연결 실패
```bash
# 연결 확인
docker exec blacklist-collector python -c "from core.database import db_service; print(db_service.test_connection())"
```

#### 2. REGTECH 인증 실패
- 인증 정보 확인
- REGTECH 포털 접근 가능 여부 확인
- 네트워크 연결 상태 확인

#### 3. 수집이 진행되지 않음
```bash
# 스케줄러 상태 확인
curl http://localhost:8545/status | jq '.scheduler'
```

#### 4. 메모리 부족
- 배치 크기 조정: `BATCH_SIZE` 환경변수 설정
- 컨테이너 메모리 제한 증가

### 로그 분석

```bash
# 상세 로그 확인
docker logs blacklist-collector --tail 200

# 에러만 필터링
docker logs blacklist-collector 2>&1 | grep -i error

# 수집 결과 확인
docker logs blacklist-collector 2>&1 | grep "수집 완료"
```

## 개발 및 디버깅

### 로컬 개발
```bash
# 의존성 설치
pip install -r requirements.txt

# 직접 실행
python collector/run_collector.py
```

### 디버그 모드
```bash
# 디버그 로그 활성화
docker run -e LOG_LEVEL=DEBUG blacklist-collector
```

## 성능 최적화

### 메모리 최적화
- 배치 크기 조정 (`BATCH_SIZE`)
- 연결 풀 크기 조정

### 네트워크 최적화
- 재시도 간격 조정 (`MAX_RETRY_ATTEMPTS`)
- 타임아웃 설정 최적화

### 데이터베이스 최적화
- 인덱스 최적화
- 배치 크기 조정

## 보안 고려사항

- 인증 정보는 환경변수로 관리
- 로그에 민감 정보 노출 방지
- 네트워크 접근 제한 (방화벽 설정)
- 정기적인 이미지 업데이트

## 모니터링 및 알림

### Prometheus 메트릭
- `collector_total_runs`: 총 실행 횟수
- `collector_successful_runs`: 성공한 실행 횟수
- `collector_failed_runs`: 실패한 실행 횟수
- `collector_total_ips`: 총 IP 개수
- `collector_active_ips`: 활성 IP 개수

### 알림 설정
- 수집 실패 시 알림
- 헬스체크 실패 시 알림
- 메모리/CPU 사용량 알림

## 버전 정보

- **Version**: 1.0.0
- **Python**: 3.9+
- **Dependencies**: requirements.txt 참조

## 라이선스

이 프로젝트는 Blacklist Management System의 일부입니다.