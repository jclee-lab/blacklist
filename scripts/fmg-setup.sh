#!/bin/bash
# FortiManager Threat Feed Setup (Simple)
# FortiManager가 Flask에서 pull → FortiGate는 FortiManager에서 pull

set -e

# === 설정 (여기만 수정) ===
FMG_HOST="${FMG_HOST:-192.168.1.100}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS}"
FMG_ADOM="${FMG_ADOM:-root}"
API_URL="https://blacklist.nxtd.co.kr/api/fortinet/active-ips"
RESOURCE_NAME="NXTD-Blacklist"
# =========================

# 필수 값 체크
if [ -z "$FMG_PASS" ]; then
    echo "Error: FMG_PASS 환경변수 필요"
    echo "사용법: FMG_PASS='password' bash $0"
    exit 1
fi

echo "=== FortiManager Threat Feed Setup ==="
echo "FortiManager: $FMG_HOST"
echo "API: $API_URL"
echo ""

# 1. Login
echo "[1/5] FortiManager 로그인..."
SESSION=$(curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{\"url\":\"/sys/login/user\",\"data\":{\"user\":\"$FMG_USER\",\"passwd\":\"$FMG_PASS\"}}],
    \"id\":1
}" | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION" ]; then
    echo "❌ 로그인 실패"
    exit 1
fi
echo "✅ 로그인 성공"

# 2. External Resource 생성 (FortiManager가 Flask API에서 pull)
echo "[2/5] External Resource 생성..."
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"set\",
    \"params\":[{
        \"url\": \"/pm/config/adom/$FMG_ADOM/obj/system/external-resource\",
        \"data\": {
            \"name\": \"$RESOURCE_NAME\",
            \"type\": \"address\",
            \"category\": 193,
            \"resource\": \"$API_URL\",
            \"refresh-rate\": 5,
            \"status\": \"enable\",
            \"comments\": \"NXTD Blacklist - FortiManager hosted\"
        }
    }],
    \"session\":\"$SESSION\",
    \"id\":2
}" > /dev/null
echo "✅ External Resource 생성"

# 3. Address Object 생성
echo "[3/5] Address Object 생성..."
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"set\",
    \"params\":[{
        \"url\": \"/pm/config/adom/$FMG_ADOM/obj/firewall/address\",
        \"data\": {
            \"name\": \"$RESOURCE_NAME\",
            \"type\": \"external-resource\",
            \"external-resource\": \"$RESOURCE_NAME\",
            \"comment\": \"NXTD Blacklist Address\"
        }
    }],
    \"session\":\"$SESSION\",
    \"id\":3
}" > /dev/null
echo "✅ Address Object 생성"

# 4. Address Group 생성
echo "[4/5] Address Group 생성..."
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"set\",
    \"params\":[{
        \"url\": \"/pm/config/adom/$FMG_ADOM/obj/firewall/addrgrp\",
        \"data\": {
            \"name\": \"NXTD-Blacklist-Group\",
            \"member\": [\"$RESOURCE_NAME\"],
            \"comment\": \"NXTD Blacklist Group\"
        }
    }],
    \"session\":\"$SESSION\",
    \"id\":4
}" > /dev/null
echo "✅ Address Group 생성"

# 5. Logout
echo "[5/5] 로그아웃..."
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{\"url\":\"/sys/logout\"}],
    \"session\":\"$SESSION\",
    \"id\":99
}" > /dev/null

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "다음 단계:"
echo "1. FortiManager GUI > Policy & Objects"
echo "2. Firewall Policy에 'NXTD-Blacklist-Group' 추가"
echo "3. Action: Deny"
echo "4. Install to FortiGates"
echo ""
echo "동작 방식:"
echo "  Flask API ← FortiManager (5분마다 pull)"
echo "  FortiManager ← FortiGates (fmg:// protocol)"
echo ""
echo "검증 (FortiManager CLI):"
echo "  diagnose system external-resource list"
echo "  show system external-resource $RESOURCE_NAME"
