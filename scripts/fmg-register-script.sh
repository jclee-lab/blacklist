#!/bin/bash
# FortiManager에 CLI Script 등록하는 스크립트
# 이 스크립트만 로컬에서 1회 실행 → FortiManager에 등록 → FortiManager가 5분마다 자동 실행

FMG_HOST="${1:-192.168.1.100}"
FMG_USER="${2:-admin}"
FMG_PASS="$3"

if [ -z "$FMG_PASS" ]; then
    echo "사용법: bash $0 <FMG_IP> <USER> <PASSWORD>"
    echo "예시: bash $0 192.168.1.100 admin mypassword"
    exit 1
fi

# CLI Script 내용 (FortiManager가 실행할 내용)
CLI_SCRIPT='execute url-get https://blacklist.nxtd.co.kr/api/fortinet/active-ips /tmp/nxtd-blacklist.txt

config system external-resource
    edit "NXTD-Blacklist"
        set type address
        set category 193
        set resource "file:///tmp/nxtd-blacklist.txt"
        set status enable
    next
end'

# Login
echo "FortiManager 로그인..."
SESSION=$(curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{\"url\":\"/sys/login/user\",\"data\":{\"user\":\"$FMG_USER\",\"passwd\":\"$FMG_PASS\"}}],
    \"id\":1
}" | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION" ]; then
    echo "❌ 로그인 실패"
    exit 1
fi

# CLI Script 등록
echo "CLI Script 등록 중..."
SCRIPT_JSON=$(echo "$CLI_SCRIPT" | jq -Rs .)

curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"set\",
    \"params\":[{
        \"url\":\"/dvmdb/adom/root/script\",
        \"data\":{
            \"name\":\"NXTD-Blacklist-Sync\",
            \"desc\":\"NXTD Blacklist Auto-Sync\",
            \"content\":$SCRIPT_JSON,
            \"type\":\"cli\"
        }
    }],
    \"session\":\"$SESSION\",
    \"id\":2
}"

echo ""
echo "✅ 완료!"
echo ""
echo "다음 단계 (FortiManager GUI):"
echo "1. Device Manager > Script"
echo "2. 'NXTD-Blacklist-Sync' 선택"
echo "3. Run > Schedule"
echo "4. Type: Recurring, Interval: 5 minutes"
echo ""

# Logout
curl -sk "https://$FMG_HOST/jsonrpc" -d "{
    \"method\":\"exec\",
    \"params\":[{\"url\":\"/sys/logout\"}],
    \"session\":\"$SESSION\",
    \"id\":99
}" > /dev/null
