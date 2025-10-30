#!/bin/bash
# REGTECH/SECUDIUM HTTPS(443) 강제 패치
# 에어갭 환경에서 80 포트 차단 시 사용

set -e

echo "🔧 HTTPS 포트 강제 패치 시작..."
echo ""

# 1. Collector 컨테이너 내부 환경변수 확인
echo "[1/4] 현재 설정 확인"
docker exec blacklist-collector env | grep -E "REGTECH_BASE_URL|SECUDIUM_BASE_URL" || echo "  (환경변수 없음)"
echo ""

# 2. Python 코드 내 URL 패치 (http:// -> https://)
echo "[2/4] Collector Python 코드 패치"
docker exec blacklist-collector bash -c "
    # REGTECH collector
    if [ -f /app/core/regtech_collector.py ]; then
        sed -i 's|http://regtech.fsec.or.kr|https://regtech.fsec.or.kr|g' /app/core/regtech_collector.py
        echo '  ✓ regtech_collector.py'
    fi
    
    # SECUDIUM collector
    if [ -f /app/core/secudium_collector.py ]; then
        sed -i 's|http://www.secudium.com|https://www.secudium.com|g' /app/core/secudium_collector.py
        sed -i 's|http://secudium.com|https://secudium.com|g' /app/core/secudium_collector.py
        echo '  ✓ secudium_collector.py'
    fi
    
    # Config 파일
    if [ -f /app/core/config.py ]; then
        sed -i 's|http://regtech.fsec.or.kr|https://regtech.fsec.or.kr|g' /app/core/config.py
        sed -i 's|http://www.secudium.com|https://www.secudium.com|g' /app/core/config.py
        echo '  ✓ config.py'
    fi
"
echo ""

# 3. 환경변수 강제 설정 (docker-compose.yml 없이)
echo "[3/4] 환경변수 재설정"
docker exec blacklist-collector bash -c "
    export REGTECH_BASE_URL='https://regtech.fsec.or.kr'
    export SECUDIUM_BASE_URL='https://www.secudium.com'
    echo '  ✓ REGTECH_BASE_URL=https://regtech.fsec.or.kr'
    echo '  ✓ SECUDIUM_BASE_URL=https://www.secudium.com'
"
echo ""

# 4. Collector 재시작
echo "[4/4] Collector 서비스 재시작"
docker restart blacklist-collector
echo "  ✓ 재시작 완료"
echo ""

# 대기
echo "⏳ 서비스 시작 대기 (10초)..."
sleep 10

# 검증
echo ""
echo "✅ 패치 완료 - 검증 중..."
docker logs blacklist-collector 2>&1 | tail -5
echo ""
echo "📡 테스트 방법:"
echo "  curl -X POST http://localhost:2542/api/collection/regtech/trigger"
echo ""
