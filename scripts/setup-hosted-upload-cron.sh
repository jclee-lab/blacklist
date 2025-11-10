#!/bin/bash
#
# Setup Cron Job for FortiManager Hosted Upload Auto-Update
#
# Usage:
#   bash setup-hosted-upload-cron.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPLOAD_SCRIPT="$SCRIPT_DIR/fortimanager-hosted-upload.sh"
ENV_FILE="$SCRIPT_DIR/../.env.fortimanager.hosted"

echo "========================================="
echo "FortiManager Hosted Upload 자동화 설정"
echo "========================================="
echo ""

# Create environment file template
if [[ ! -f "$ENV_FILE" ]]; then
    cat > "$ENV_FILE" << 'EOF'
# FortiManager Configuration
FMG_HOST=192.168.1.100
FMG_USER=admin
FMG_PASS=your_password_here

# API Configuration
API_URL=https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text
EOF

    echo "✅ Environment template created: $ENV_FILE"
    echo ""
    echo "📝 Please edit $ENV_FILE and set correct values:"
    echo "   - FMG_HOST: FortiManager IP/hostname"
    echo "   - FMG_PASS: FortiManager password"
    echo ""
    echo "vi $ENV_FILE"
    echo ""
    read -r -p "Press Enter after editing the file..."
fi

# Validate environment file
if ! grep -q "^FMG_HOST=" "$ENV_FILE" || ! grep -q "^FMG_PASS=" "$ENV_FILE"; then
    echo "❌ Environment file not configured properly"
    exit 1
fi

# Source the env file to check values
source "$ENV_FILE"

if [[ "$FMG_PASS" == "your_password_here" ]]; then
    echo "❌ Please set FMG_PASS in $ENV_FILE"
    exit 1
fi

# Create cron wrapper script
CRON_WRAPPER="$SCRIPT_DIR/hosted-upload-cron-wrapper.sh"
cat > "$CRON_WRAPPER" << EOF
#!/bin/bash
set -a
source "$ENV_FILE"
set +a
"$UPLOAD_SCRIPT" >> /var/log/fortimanager-hosted-upload.log 2>&1
EOF

chmod +x "$CRON_WRAPPER"

# Ask for cron schedule
echo ""
echo "Cron 스케줄 선택:"
echo "  1) 10분마다 (권장)"
echo "  2) 5분마다"
echo "  3) 30분마다"
echo "  4) 매시간 정각"
echo "  5) 하루 1번 (오전 2시)"
echo "  6) 커스텀"
echo ""
read -r -p "선택 (1-6): " schedule_choice

case "$schedule_choice" in
    1)
        CRON_SCHEDULE="*/10 * * * *"
        CRON_DESC="10분마다"
        ;;
    2)
        CRON_SCHEDULE="*/5 * * * *"
        CRON_DESC="5분마다"
        ;;
    3)
        CRON_SCHEDULE="*/30 * * * *"
        CRON_DESC="30분마다"
        ;;
    4)
        CRON_SCHEDULE="0 * * * *"
        CRON_DESC="매시간 정각"
        ;;
    5)
        CRON_SCHEDULE="0 2 * * *"
        CRON_DESC="매일 오전 2시"
        ;;
    6)
        echo ""
        echo "Cron 형식 예시: */10 * * * *  (10분마다)"
        read -r -p "Cron 스케줄 입력: " CRON_SCHEDULE
        CRON_DESC="커스텀 스케줄"
        ;;
    *)
        echo "❌ 잘못된 선택"
        exit 1
        ;;
esac

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "$CRON_WRAPPER"; then
    echo ""
    echo "⚠️ Cron job이 이미 존재합니다:"
    crontab -l | grep "$CRON_WRAPPER"
    echo ""
    read -r -p "기존 cron을 삭제하고 새로 추가하시겠습니까? (y/n): " replace

    if [[ "$replace" == "y" || "$replace" == "Y" ]]; then
        # Remove old cron
        crontab -l 2>/dev/null | grep -v "$CRON_WRAPPER" | crontab -
        echo "✅ 기존 cron 삭제됨"
    else
        echo "취소됨"
        exit 0
    fi
fi

# Add cron job
CRON_ENTRY="$CRON_SCHEDULE $CRON_WRAPPER"
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo ""
echo "========================================="
echo "✅ Cron job 설정 완료!"
echo "========================================="
echo ""
echo "📋 설정 정보:"
echo "  - 스케줄: $CRON_DESC"
echo "  - Cron: $CRON_SCHEDULE"
echo "  - 스크립트: $CRON_WRAPPER"
echo "  - 환경설정: $ENV_FILE"
echo ""
echo "📋 로그 확인:"
echo "  tail -f /var/log/fortimanager-hosted-upload.log"
echo ""
echo "📋 현재 cron 목록:"
crontab -l | grep fortimanager
echo ""
echo "📋 즉시 테스트:"
echo "  bash $CRON_WRAPPER"
echo ""
echo "📋 cron 삭제 방법:"
echo "  crontab -e  # 그리고 해당 라인 삭제"
echo ""

# Ask if user wants to test now
read -r -p "지금 즉시 테스트 실행하시겠습니까? (y/n): " test_now

if [[ "$test_now" == "y" || "$test_now" == "Y" ]]; then
    echo ""
    echo "========================================="
    echo "테스트 실행 중..."
    echo "========================================="
    bash "$CRON_WRAPPER"
    echo ""
    echo "테스트 완료! 로그를 확인하세요:"
    echo "  tail -20 /var/log/fortimanager-hosted-upload.log"
fi

exit 0
