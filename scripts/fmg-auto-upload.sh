#!/bin/bash
# FortiManager 자동 업로드 스크립트
# Flask API → FortiManager → FortiGates

set -e

# === 설정 ===
FMG_HOST="${1:-192.168.1.100}"
FMG_USER="${2:-admin}"
FMG_PASS="$3"
API_URL="https://blacklist.nxtd.co.kr/api/fortinet/active-ips"
RESOURCE_NAME="NXTD-Blacklist"
TMP_FILE="/tmp/nxtd-blacklist.txt"

if [ -z "$FMG_PASS" ]; then
    echo "사용법: bash $0 <FMG_IP> <USER> <PASSWORD>"
    echo "예시: bash $0 192.168.1.100 admin mypass123"
    exit 1
fi

echo "=== FortiManager Auto Upload ==="
echo "FortiManager: $FMG_HOST"
echo "API: $API_URL"
echo ""

# 1. Flask API에서 다운로드
echo "[1/4] Flask API에서 IP 리스트 다운로드..."
if ! curl -sf "$API_URL" -o "$TMP_FILE"; then
    echo "❌ API 다운로드 실패"
    exit 1
fi
IP_COUNT=$(wc -l < "$TMP_FILE")
echo "✅ Downloaded $IP_COUNT IPs"

# 2. FortiManager 로그인
echo "[2/4] FortiManager 로그인..."
SESSION=$(curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{
        \"url\":\"/sys/login/user\",
        \"data\":{\"user\":\"$FMG_USER\",\"passwd\":\"$FMG_PASS\"}
    }],
    \"id\":1
}" | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION" ]; then
    echo "❌ 로그인 실패"
    exit 1
fi
echo "✅ 로그인 성공"

# 3. 파일을 Base64로 인코딩하여 업로드
echo "[3/4] FortiManager에 파일 업로드..."
FILE_CONTENT=$(cat "$TMP_FILE" | base64 -w 0)

UPLOAD_RESULT=$(curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{
        \"url\":\"/sys/proxy/json\",
        \"data\":{
            \"action\":\"set\",
            \"resource\":\"/api/v2/cmdb/system/external-resource\",
            \"payload\":{
                \"name\":\"$RESOURCE_NAME\",
                \"type\":\"address\",
                \"category\":193,
                \"resource\":\"data:text/plain;base64,$FILE_CONTENT\",
                \"status\":\"enable\",
                \"comments\":\"NXTD Blacklist - Auto uploaded $(date +'%Y-%m-%d %H:%M:%S')\"
            }
        }
    }],
    \"session\":\"$SESSION\",
    \"id\":2
}")

echo "✅ 파일 업로드 완료"

# 4. 로그아웃
echo "[4/4] 로그아웃..."
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{\"url\":\"/sys/logout\"}],
    \"session\":\"$SESSION\",
    \"id\":99
}" > /dev/null

rm -f "$TMP_FILE"

echo ""
echo "=== ✅ 완료 ==="
echo "업로드: $IP_COUNT IPs"
echo ""
echo "FortiGate 설정 (CLI):"
echo "  config system external-resource"
echo "      edit \"$RESOURCE_NAME\""
echo "          set type address"
echo "          set resource \"fmg://$RESOURCE_NAME\""
echo "          set status enable"
echo "      next"
echo "  end"
echo ""
echo "Cron 등록 (5분마다):"
echo "  */5 * * * * bash $(realpath $0) $FMG_HOST $FMG_USER '$FMG_PASS' >> /var/log/fmg-upload.log 2>&1"
echo ""
