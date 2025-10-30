#!/bin/bash
# FortiManager UI 통합 테스트 스크립트

set -e

echo "🔍 FortiManager UI 통합 테스트"
echo "========================================"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. API 엔드포인트 확인
echo ""
echo "📡 Step 1: API 엔드포인트 확인"
echo "--------------------------------------"

if curl -s -f http://localhost:2542/collection-panel/api/load-credentials > /dev/null; then
    echo -e "${GREEN}✅ API 엔드포인트 응답 정상${NC}"
else
    echo -e "${RED}❌ API 엔드포인트 응답 없음${NC}"
    echo "   서비스가 실행 중인지 확인하세요: docker compose ps"
    exit 1
fi

# 2. 인증정보 로드 테스트
echo ""
echo "🔐 Step 2: 인증정보 조회"
echo "--------------------------------------"

CREDS=$(curl -s http://localhost:2542/collection-panel/api/load-credentials)
echo "$CREDS" | jq .

if echo "$CREDS" | jq -e '.success == true' > /dev/null; then
    echo -e "${GREEN}✅ 인증정보 로드 성공${NC}"
else
    echo -e "${RED}❌ 인증정보 로드 실패${NC}"
    exit 1
fi

# 3. FortiManager 설정 확인
echo ""
echo "🔧 Step 3: FortiManager 설정 확인"
echo "--------------------------------------"

FMG_HOST=$(echo "$CREDS" | jq -r '.credentials.fmg_host // empty')
FMG_ENABLED=$(echo "$CREDS" | jq -r '.credentials.fmg_upload_enabled // false')

if [ -n "$FMG_HOST" ]; then
    echo -e "${GREEN}✅ FortiManager Host: $FMG_HOST${NC}"
    echo "   Enabled: $FMG_ENABLED"
else
    echo -e "${YELLOW}⚠️  FortiManager 설정 없음${NC}"
    echo "   UI에서 설정을 추가하세요: https://blacklist.nxtd.co.kr/collection-panel"
    echo ""
    echo "   테스트 설정 추가 (예시):"
    echo "   curl -X POST http://localhost:2542/collection-panel/api/save-credentials \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{
        \"fmg_host\": \"192.168.1.100\",
        \"fmg_user\": \"admin\",
        \"fmg_password\": \"test_password\",
        \"fmg_upload_enabled\": true,
        \"fmg_upload_interval\": 300
      }'"
fi

# 4. Database 확인
echo ""
echo "💾 Step 4: Database 직접 확인"
echo "--------------------------------------"

DB_CHECK=$(PGPASSWORD=postgres docker exec blacklist-postgres psql -U postgres -d blacklist -t -c \
"SELECT service_name, username, config->>'host' as host, config->>'enabled' as enabled
 FROM collection_credentials
 WHERE service_name = 'FORTIMANAGER';" 2>/dev/null || echo "ERROR")

if [ "$DB_CHECK" != "ERROR" ]; then
    if [ -n "$DB_CHECK" ]; then
        echo -e "${GREEN}✅ Database에 FortiManager 설정 존재${NC}"
        echo "$DB_CHECK"
    else
        echo -e "${YELLOW}⚠️  Database에 FortiManager 설정 없음${NC}"
    fi
else
    echo -e "${RED}❌ Database 접근 실패${NC}"
    echo "   컨테이너 상태 확인: docker compose ps blacklist-postgres"
fi

# 5. Uploader 스크립트 테스트
echo ""
echo "🚀 Step 5: FortiManager Uploader 스크립트 존재 확인"
echo "--------------------------------------"

if docker exec blacklist-collector test -f /app/collector/fortimanager_uploader.py; then
    echo -e "${GREEN}✅ Uploader 스크립트 존재${NC}"
    echo "   위치: /app/collector/fortimanager_uploader.py"
else
    echo -e "${RED}❌ Uploader 스크립트 없음${NC}"
    echo "   collector 컨테이너를 재빌드 하세요"
    exit 1
fi

# 6. 수동 업로드 테스트 (dry-run)
echo ""
echo "🧪 Step 6: Uploader 실행 가능 확인"
echo "--------------------------------------"

if [ "$FMG_ENABLED" = "true" ] && [ -n "$FMG_HOST" ]; then
    echo "FortiManager 설정이 활성화되어 있습니다."
    echo ""
    echo "수동 업로드 테스트 실행:"
    echo "  docker exec blacklist-collector python /app/collector/fortimanager_uploader.py"
    echo ""
    read -p "지금 실행하시겠습니까? (y/N): " CONFIRM

    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        echo ""
        echo "실행 중..."
        docker exec blacklist-collector python /app/collector/fortimanager_uploader.py
    else
        echo "건너뛰기"
    fi
else
    echo -e "${YELLOW}⚠️  FortiManager 설정이 비활성화되어 있거나 Host가 설정되지 않았습니다${NC}"
    echo "   UI에서 설정을 활성화하세요"
fi

# 요약
echo ""
echo "========================================"
echo "✨ 테스트 완료"
echo "========================================"
echo ""
echo "다음 단계:"
echo "  1. UI 설정: https://blacklist.nxtd.co.kr/collection-panel"
echo "  2. FortiManager 인증정보 입력"
echo "  3. 저장 후 수동 업로드 테스트"
echo "  4. FortiManager에서 확인: System > External Resources"
echo ""
