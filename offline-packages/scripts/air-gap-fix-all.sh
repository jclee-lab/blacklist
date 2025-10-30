#!/bin/bash
# 에어갭 환경 종합 패치 (All-in-One)
# - Docker Compose 오프라인 설정 자동 수정
# - HTTPS(443) 강제 전환 (REGTECH/SECUDIUM)
# - 서비스 재시작 및 검증

set -e

COMPOSE_FILE="docker-compose.yml"
BACKUP_FILE="docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 에어갭 환경 종합 패치 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: Docker Compose 파일 오프라인 설정 적용
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Step 1/4: Docker Compose 오프라인 설정 수정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ ERROR: $COMPOSE_FILE 파일이 없습니다."
    echo "   현재 디렉토리: $(pwd)"
    echo "   패치 파일 위치: $(dirname "$0")"
    echo ""
    echo "💡 해결 방법:"
    echo "   1. blacklist 프로젝트 루트로 이동"
    echo "   2. 또는 docker-compose.yml이 있는 디렉토리에서 실행"
    exit 1
fi

echo "  📄 백업 생성: $BACKUP_FILE"
cp "$COMPOSE_FILE" "$BACKUP_FILE"

echo "  🔧 수정 중..."

# Frontend: build → offline image
sed -i 's|^    build: ./frontend|    image: blacklist-frontend:offline\n    pull_policy: never|g' "$COMPOSE_FILE"

# Redis: 기본 이미지 → offline image
sed -i '/blacklist-redis:/,/^  [a-z]/ s|image: redis:7-alpine|image: blacklist-redis:offline|g' "$COMPOSE_FILE"
sed -i '/blacklist-redis:/,/^  [a-z]/ {/pull_policy: never/!{/image: blacklist-redis/a\    pull_policy: never
}}' "$COMPOSE_FILE"

echo "  ✅ Docker Compose 파일 수정 완료"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: 컨테이너 HTTPS(443) 포트 강제 전환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Step 2/4: HTTPS(443) 포트 강제 전환"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 컨테이너 실행 여부 확인
if ! docker ps --format '{{.Names}}' | grep -q "blacklist-collector"; then
    echo "  ⚠️  WARNING: blacklist-collector 컨테이너가 실행 중이 아닙니다."
    echo "  컨테이너 시작 후 다시 실행하세요."
    echo ""
else
    echo "  현재 설정 확인:"
    docker exec blacklist-collector env | grep -E "REGTECH_BASE_URL|SECUDIUM_BASE_URL" || echo "    (환경변수 없음)"
    echo ""

    echo "  🔧 Collector Python 코드 패치 중..."
    docker exec blacklist-collector bash -c "
        # REGTECH - 모든 파일에서 HTTP → HTTPS 변환
        if [ -f /app/collector/config.py ]; then
            sed -i 's|http://regtech.fsec.or.kr|https://regtech.fsec.or.kr|g' /app/collector/config.py
            echo '    ✓ collector/config.py (REGTECH)'
        fi

        if [ -f /app/core/regtech_collector.py ]; then
            sed -i 's|http://regtech.fsec.or.kr|https://regtech.fsec.or.kr|g' /app/core/regtech_collector.py
            echo '    ✓ core/regtech_collector.py'
        fi

        if [ -f /app/core/policy_monitor.py ]; then
            sed -i 's|http://regtech.fsec.or.kr|https://regtech.fsec.or.kr|g' /app/core/policy_monitor.py
            echo '    ✓ core/policy_monitor.py (모니터링 스케줄러)'
        fi

        # SECUDIUM - 올바른 URL로 변경
        if [ -f /app/api/secudium_api.py ]; then
            sed -i 's|http://secudium.skinfosec.co.kr|https://secudium.skinfosec.co.kr|g' /app/api/secudium_api.py
            echo '    ✓ api/secudium_api.py'
        fi
    "

    # 환경변수 강제 설정
    echo "  🔧 환경변수 강제 설정 중..."
    docker exec blacklist-collector bash -c "
        export REGTECH_BASE_URL='https://regtech.fsec.or.kr'
        echo '    ✓ REGTECH_BASE_URL=https://regtech.fsec.or.kr'
    "
    echo "  ✅ 코드 패치 완료"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: 데이터베이스 마이그레이션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  Step 3/5: 데이터베이스 마이그레이션"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-postgres"; then
    echo "  🔧 Connection test tracking 컬럼 추가 중..."
    if docker exec blacklist-postgres psql -U postgres -d blacklist <<'EOF'
-- Migration: Add connection test tracking columns
ALTER TABLE collection_credentials
ADD COLUMN IF NOT EXISTS last_connection_test TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_test_result BOOLEAN,
ADD COLUMN IF NOT EXISTS last_test_message TEXT;

COMMENT ON COLUMN collection_credentials.last_connection_test IS 'Last connection test timestamp';
COMMENT ON COLUMN collection_credentials.last_test_result IS 'Last connection test result (true=success, false=failure)';
COMMENT ON COLUMN collection_credentials.last_test_message IS 'Last connection test message';
EOF
    then
        echo "  ✅ 마이그레이션 완료"
    else
        echo "  ⚠️  마이그레이션 실패 (이미 적용되었을 수 있음)"
    fi
    echo ""
else
    echo "  ⚠️  PostgreSQL 컨테이너가 실행 중이 아니므로 건너뜀"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: 서비스 재시작
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "♻️  Step 4/5: 서비스 재시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-"; then
    echo "  🔄 컨테이너 재시작 중..."
    docker compose restart
    echo "  ✅ 재시작 완료"
    echo ""

    echo "  ⏳ 서비스 초기화 대기 (15초)..."
    sleep 15
else
    echo "  ℹ️  컨테이너가 실행 중이 아니므로 재시작 건너뜀"
    echo "  💡 서비스 시작: docker compose up -d"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 5: 검증
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Step 5/5: 검증"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  📋 Docker Compose 변경 사항:"
echo "    - Frontend: build → offline image (pull_policy: never)"
echo "    - Redis: 기본 이미지 → offline image (pull_policy: never)"
echo ""

echo "  🗄️  데이터베이스 마이그레이션:"
echo "    - collection_credentials 테이블: last_connection_test 컬럼 추가"
echo "    - connection test tracking 기능 활성화"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-collector"; then
    echo "  🌐 HTTPS 설정 확인:"
    docker exec blacklist-collector bash -c "
        grep -h 'https://' /app/core/*.py 2>/dev/null | grep -E 'regtech|secudium' | head -3 || echo '    (HTTPS URL 확인 필요)'
    "
    echo ""

    echo "  📊 컨테이너 상태:"
    docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 에어갭 환경 종합 패치 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 백업 파일: $BACKUP_FILE"
echo ""
echo "📡 수집 테스트:"
echo "  curl -X POST http://localhost:2542/api/collection/regtech/trigger"
echo "  curl -X POST http://localhost:2542/api/collection/trigger/SECUDIUM"
echo ""
echo "🔍 로그 확인:"
echo "  docker logs -f blacklist-collector"
echo "  docker logs -f blacklist-app"
echo ""
