# Docker Image Manifest - v3.4.0

## 📦 Packaged Images

**Location**: `dist/images/`
**Total Size**: 829MB
**Build Date**: 2025-11-08

### Image List

| Image | Size | File | SHA256 |
|-------|------|------|--------|
| blacklist-app | 144MB | `blacklist-app_20251108_080645.tar.gz` | 계산 필요 |
| blacklist-collector | 486MB | `blacklist-collector_20251108_080711.tar.gz` | 계산 필요 |
| blacklist-frontend | 67MB | `blacklist-frontend_20251108_080525.tar.gz` | 계산 필요 |
| blacklist-postgres | 101MB | `blacklist-postgres_20251108_080628.tar.gz` | 계산 필요 |
| blacklist-redis | 17MB | `blacklist-redis_20251108_080601.tar.gz` | 계산 필요 |

**Note**: Redis 이미지 중복 파일 발견 (`blacklist-redis_20251108_080610.tar.gz`) - 정리 필요

## 🔨 빌드 정보

### Build Environment
- Docker BuildKit: Enabled
- Multi-stage builds: Yes
- Base Images:
  - App: python:3.11-slim
  - Collector: python:3.11-slim + playwright
  - Frontend: node:18-alpine
  - PostgreSQL: postgres:15-alpine
  - Redis: redis:7-alpine

### Build Commands
```bash
# 단일 이미지 패키징
./scripts/package-single-image.sh blacklist-app

# 모든 이미지 순차 패키징
./scripts/package-all-sequential.sh

# 패키지 무결성 검증
sha256sum dist/images/*.tar.gz
```

## 🚀 배포 방법

### 1. Air-Gapped 서버로 전송
```bash
# USB 또는 외장 HDD로 복사
cp dist/images/*.tar.gz /media/usb/

# 또는 SCP (임시 연결 가능 시)
scp dist/images/*.tar.gz airgap-server:/opt/blacklist/images/
```

### 2. 이미지 로드
```bash
cd /opt/blacklist/images

# 모든 이미지 로드
for f in *.tar.gz; do
    echo "[LOAD] Loading $f..."
    gunzip -c "$f" | docker load
done

# 로드 확인
docker images | grep blacklist
```

### 3. 서비스 시작
```bash
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml up -d

# 헬스 체크
curl http://localhost:2542/health
```

## 📊 이미지 상세 정보

### blacklist-app (144MB)
- Base: python:3.11-slim
- 주요 패키지: Flask, SQLAlchemy, Redis, psycopg2
- 포트: 2542
- 헬스체크: `/health` endpoint

### blacklist-collector (486MB)
- Base: python:3.11-slim
- 주요 패키지: Playwright (브라우저 포함), Requests, BeautifulSoup
- 포트: 8545 (내부)
- 헬스체크: `/health` endpoint

### blacklist-frontend (67MB)
- Base: node:18-alpine
- Framework: Next.js 13
- 포트: 2543
- SSR: Enabled

### blacklist-postgres (101MB)
- Base: postgres:15-alpine
- Extensions: pg_stat_statements
- 포트: 5432 (내부)
- Auto-migration: Enabled

### blacklist-redis (17MB)
- Base: redis:7-alpine
- Persistence: AOF enabled
- 포트: 6379 (내부)
- 메모리 제한: 512MB

## 🔒 보안 사항

### Image Security
- Non-root execution: ✅
- Multi-stage builds: ✅
- Minimal base images: ✅
- No secrets in images: ✅

### Vulnerability Scanning
```bash
# Trivy 스캔 (권장)
trivy image blacklist-app:latest

# Docker scan
docker scan blacklist-app:latest
```

## 📝 Known Issues

1. **Redis 중복 이미지**: `blacklist-redis_20251108_080610.tar.gz` 제거 필요
2. **Collector 이미지 크기**: Playwright 포함으로 486MB로 큼 - 최적화 검토 필요

## 🔄 업데이트 이력

### v3.4.0 (2025-11-08)
- 초기 이미지 매니페스트 생성
- 5개 서비스 이미지 패키징 완료

---

**참고 문서**:
- [IMAGE-PACKAGING-COMPLETE.md](../../../IMAGE-PACKAGING-COMPLETE.md)
- [CLAUDE.md](../../../CLAUDE.md) - Air-Gapped Deployment 섹션
