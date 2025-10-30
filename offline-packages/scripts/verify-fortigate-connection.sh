#!/bin/bash
# FortiGate/FortiManager 연동 확인 스크립트

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 FortiGate/FortiManager 연동 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: API 테스트 (로컬)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Step 1: API 엔드포인트 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  🧪 1-1. Health Check"
if docker exec blacklist-app curl -s http://localhost:2542/api/fortinet/health 2>/dev/null | grep -q '"status"'; then
    echo "    ✅ API 응답 정상"
    docker exec blacklist-app curl -s http://localhost:2542/api/fortinet/health 2>/dev/null | python3 -m json.tool 2>/dev/null | head -10
else
    echo "    ❌ API 응답 없음"
fi
echo ""

echo "  🧪 1-2. Threat Feed (FortiGate 형식)"
THREAT_FEED=$(docker exec blacklist-app curl -s http://localhost:2542/api/fortinet/threat-feed 2>/dev/null)
if echo "$THREAT_FEED" | grep -q '"commands"'; then
    echo "    ✅ Threat Feed 정상"
    IP_COUNT=$(echo "$THREAT_FEED" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('commands', [{}])[0].get('entries', [])))" 2>/dev/null || echo "0")
    echo "    📊 IP 개수: ${IP_COUNT}개"
else
    echo "    ❌ Threat Feed 응답 없음"
fi
echo ""

echo "  🧪 1-3. Block List (텍스트 형식)"
BLOCKLIST=$(docker exec blacklist-app curl -s http://localhost:2542/api/fortinet/blocklist 2>/dev/null)
if echo "$BLOCKLIST" | grep -q '"blocklist"'; then
    echo "    ✅ Block List 정상"
    IP_COUNT=$(echo "$BLOCKLIST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('blocklist', '').split('\n')))" 2>/dev/null || echo "0")
    echo "    📊 IP 개수: ${IP_COUNT}개"
    echo ""
    echo "    샘플 IP (처음 5개):"
    echo "$BLOCKLIST" | python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join(data.get('blocklist', '').split('\n')[:5]))" 2>/dev/null || echo "    (없음)"
else
    echo "    ❌ Block List 응답 없음"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: 데이터베이스 IP 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  Step 2: 데이터베이스 IP 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "blacklist-postgres"; then
    echo "  📊 Blacklist IP 통계:"
    docker exec blacklist-postgres psql -U postgres -d blacklist -c "
        SELECT
            COUNT(*) as total_ips,
            COUNT(CASE WHEN is_active = true THEN 1 END) as active_ips,
            COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_ips,
            COUNT(DISTINCT country) as unique_countries
        FROM blacklist_ips;
    " 2>/dev/null || echo "    ❌ DB 쿼리 실패"
    echo ""

    echo "  🌍 국가별 상위 5개:"
    docker exec blacklist-postgres psql -U postgres -d blacklist -c "
        SELECT country, COUNT(*) as count
        FROM blacklist_ips
        WHERE is_active = true
        GROUP BY country
        ORDER BY count DESC
        LIMIT 5;
    " 2>/dev/null || echo "    ❌ DB 쿼리 실패"
    echo ""

    echo "  📋 최근 IP 5개 (샘플):"
    docker exec blacklist-postgres psql -U postgres -d blacklist -c "
        SELECT ip_address, country, reason, detection_date
        FROM blacklist_ips
        WHERE is_active = true
        ORDER BY detection_date DESC
        LIMIT 5;
    " 2>/dev/null || echo "    ❌ DB 쿼리 실패"
    echo ""
else
    echo "  ⚠️  PostgreSQL 컨테이너 실행 중이 아님"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: 접속 로그 확인 (FortiGate에서 접근했는지)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Step 3: FortiGate 접속 로그 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  🔍 Nginx Access Log (최근 20줄, FortiGate API 호출):"
if docker ps --format '{{.Names}}' | grep -q "blacklist-nginx"; then
    FORTINET_LOGS=$(docker logs blacklist-nginx 2>&1 | grep "/api/fortinet" | tail -20)
    if [ -n "$FORTINET_LOGS" ]; then
        echo "$FORTINET_LOGS" | awk '{print "    " $0}'
        echo ""
        echo "  📊 API 호출 통계:"
        echo "$FORTINET_LOGS" | awk '{print $7}' | sort | uniq -c | sort -rn | awk '{print "    " $2 " - " $1 "회"}'
    else
        echo "    ℹ️  FortiGate API 호출 로그 없음 (아직 FortiGate가 접속하지 않음)"
    fi
else
    echo "    ⚠️  Nginx 컨테이너 실행 중이 아님"
fi
echo ""

echo "  🔍 App Access Log (최근 10줄, FortiGate API):"
APP_FORTINET_LOGS=$(docker logs blacklist-app 2>&1 | grep "/api/fortinet" | tail -10)
if [ -n "$APP_FORTINET_LOGS" ]; then
    echo "$APP_FORTINET_LOGS" | awk '{print "    " $0}'
else
    echo "    ℹ️  App에서 FortiGate API 호출 로그 없음"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: 실시간 모니터링 가이드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Step 4: 실시간 모니터링 방법"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat <<'EOF'
  📡 1. 실시간 로그 모니터링 (FortiGate 접속 감지)

     # Nginx 로그 (FortiGate 접속 시 표시)
     docker logs -f blacklist-nginx 2>&1 | grep --line-buffered "/api/fortinet"

     # App 로그
     docker logs -f blacklist-app 2>&1 | grep --line-buffered "/api/fortinet"


  🧪 2. 외부 테스트 (FortiGate 대신 직접 호출)

     # Threat Feed 테스트
     curl -sk https://blacklist.nxtd.co.kr/api/fortinet/threat-feed | jq .

     # Block List 테스트
     curl -sk https://blacklist.nxtd.co.kr/api/fortinet/blocklist | jq .

     # Health Check
     curl -sk https://blacklist.nxtd.co.kr/api/fortinet/health | jq .


  🔍 3. FortiGate에서 확인

     # FortiGate CLI
     diagnose debug application httpsd -1
     diagnose debug enable

     # External Resource 상태 확인
     diagnose test application update_engine 8

     # Threat Feed 업데이트 강제 실행
     execute update-now


  📊 4. 통계 확인

     # API 호출 횟수
     docker logs blacklist-nginx 2>&1 | grep -c "/api/fortinet"

     # IP별 호출 횟수
     docker logs blacklist-nginx 2>&1 | grep "/api/fortinet" | awk '{print $1}' | sort | uniq -c

EOF

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 완료
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FortiGate 연동 확인 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 FortiGate 설정 후 다시 실행하면 접속 로그를 확인할 수 있습니다."
echo ""
