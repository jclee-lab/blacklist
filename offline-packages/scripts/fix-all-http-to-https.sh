#!/bin/bash
# 전체 HTTP → HTTPS 강제 변환 패치
# 모든 컨테이너의 Python 코드에서 REGTECH/SECUDIUM HTTP URL을 HTTPS로 변경

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 전체 HTTP → HTTPS 강제 변환 패치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: blacklist-collector 컨테이너 패치
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 1: blacklist-collector 패치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! docker ps --format '{{.Names}}' | grep -q "blacklist-collector"; then
    echo "  ⚠️  WARNING: blacklist-collector 컨테이너가 실행 중이 아닙니다."
    echo ""
else
    echo "  🔍 HTTP URL 검색 중..."
    HTTP_COUNT=$(docker exec blacklist-collector bash -c "find /app -name '*.py' -exec grep -l 'http://regtech\|http://secudium' {} \; 2>/dev/null | wc -l")
    echo "  발견된 파일: ${HTTP_COUNT}개"
    echo ""

    echo "  🔧 전체 Python 파일 변환 중..."
    docker exec blacklist-collector bash -c '
        # /app 전체에서 재귀적으로 변환
        find /app -name "*.py" -type f -exec sed -i \
            -e "s|http://regtech\.fsec\.or\.kr|https://regtech.fsec.or.kr|g" \
            -e "s|http://www\.regtech\.fsec\.or\.kr|https://regtech.fsec.or.kr|g" \
            -e "s|http://secudium\.skinfosec\.co\.kr|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://www\.secudium\.skinfosec\.co\.kr|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://secudium\.com|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://www\.secudium\.com|https://secudium.skinfosec.co.kr|g" \
            {} \;

        echo "    ✓ Python 파일 변환 완료"
    '

    echo "  🔧 환경변수 강제 설정..."
    docker exec blacklist-collector bash -c "
        # .bashrc에 추가 (영구 설정)
        if ! grep -q 'REGTECH_BASE_URL' /root/.bashrc 2>/dev/null; then
            echo 'export REGTECH_BASE_URL=\"https://regtech.fsec.or.kr\"' >> /root/.bashrc
        fi
    "

    echo "  ✅ blacklist-collector 패치 완료"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: blacklist-app 컨테이너 패치
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 2: blacklist-app 패치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! docker ps --format '{{.Names}}' | grep -q "blacklist-app"; then
    echo "  ⚠️  WARNING: blacklist-app 컨테이너가 실행 중이 아닙니다."
    echo ""
else
    echo "  🔍 HTTP URL 검색 중..."
    HTTP_COUNT=$(docker exec blacklist-app bash -c "find /app -name '*.py' -exec grep -l 'http://regtech\|http://secudium' {} \; 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    echo "  발견된 파일: ${HTTP_COUNT}개"
    echo ""

    echo "  🔧 전체 Python 파일 변환 중..."
    docker exec blacklist-app bash -c '
        # /app 전체에서 재귀적으로 변환
        find /app -name "*.py" -type f -exec sed -i \
            -e "s|http://regtech\.fsec\.or\.kr|https://regtech.fsec.or.kr|g" \
            -e "s|http://www\.regtech\.fsec\.or\.kr|https://regtech.fsec.or.kr|g" \
            -e "s|http://secudium\.skinfosec\.co\.kr|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://www\.secudium\.skinfosec\.co\.kr|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://secudium\.com|https://secudium.skinfosec.co.kr|g" \
            -e "s|http://www\.secudium\.com|https://secudium.skinfosec.co.kr|g" \
            {} \; 2>/dev/null || true

        echo "    ✓ Python 파일 변환 완료"
    '

    echo "  ✅ blacklist-app 패치 완료"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: 검증
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Step 3: 검증"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-collector"; then
    echo "  📊 Collector 남은 HTTP URL 확인:"
    REMAINING=$(docker exec blacklist-collector bash -c "find /app -name '*.py' -exec grep -n 'http://regtech\|http://secudium' {} + 2>/dev/null | wc -l")
    if [ "$REMAINING" -eq 0 ]; then
        echo "    ✅ HTTP URL 없음 (모두 변환 완료)"
    else
        echo "    ⚠️  남은 HTTP URL: ${REMAINING}개"
        echo ""
        echo "  상세 내역:"
        docker exec blacklist-collector bash -c "find /app -name '*.py' -exec grep -Hn 'http://regtech\|http://secudium' {} + 2>/dev/null | head -10"
    fi
    echo ""
fi

if docker ps --format '{{.Names}}' | grep -q "blacklist-app"; then
    echo "  📊 App 남은 HTTP URL 확인:"
    REMAINING=$(docker exec blacklist-app bash -c "find /app -name '*.py' -exec grep -n 'http://regtech\|http://secudium' {} + 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    if [ "$REMAINING" -eq 0 ]; then
        echo "    ✅ HTTP URL 없음 (모두 변환 완료)"
    else
        echo "    ⚠️  남은 HTTP URL: ${REMAINING}개"
    fi
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: 서비스 재시작
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "♻️  Step 4: 서비스 재시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-"; then
    echo "  🔄 컨테이너 재시작 중..."
    docker compose restart blacklist-collector blacklist-app 2>/dev/null || \
        docker restart blacklist-collector blacklist-app 2>/dev/null || true

    echo "  ⏳ 서비스 초기화 대기 (15초)..."
    sleep 15
    echo "  ✅ 재시작 완료"
    echo ""
else
    echo "  ℹ️  실행 중인 컨테이너 없음"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 완료
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 전체 HTTP → HTTPS 변환 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 변환된 URL:"
echo "  • http://regtech.fsec.or.kr → https://regtech.fsec.or.kr"
echo "  • http://secudium.skinfosec.co.kr → https://secudium.skinfosec.co.kr"
echo "  • http://www.secudium.com → https://secudium.skinfosec.co.kr"
echo ""
echo "🧪 테스트 방법:"
echo "  1. 로그 확인:"
echo "     docker logs blacklist-collector --tail 50 | grep https://"
echo ""
echo "  2. 수집 테스트:"
echo "     curl -X POST http://localhost:2542/api/collection/regtech/trigger"
echo ""
echo "  3. HTTP URL 재확인:"
echo "     bash $0  # 이 스크립트 재실행"
echo ""
