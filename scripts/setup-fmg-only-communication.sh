#!/bin/bash
#
# FortiManager-Only Communication Setup
#
# Purpose:
#   - FortiManager만 인터넷 연결
#   - FortiGate는 FortiManager하고만 통신 (인터넷 불필요)
#
# Architecture:
#   Blacklist API → FortiManager (5분마다) → FortiGates (fmg://)
#
# Requirements:
#   - FortiManager 7.0+ (File Upload 지원)
#   - FortiManager → Internet 연결 필요
#   - FortiGate → Internet 불필요 ✅
#
# Usage:
#   bash setup-fmg-only-communication.sh

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
info() { echo -e "${BLUE}[INFO]${NC} $*"; }

cat << 'BANNER'
╔═══════════════════════════════════════════════════════════╗
║  FortiManager-Only Communication Setup                    ║
║  FortiGate는 FortiManager하고만 통신 (인터넷 불필요)      ║
╚═══════════════════════════════════════════════════════════╝
BANNER

echo ""

# Step 1: Validation
log "Step 1: Checking prerequisites..."

if [[ ! -f ".env.fortimanager" ]]; then
    error ".env.fortimanager not found"
    echo ""
    echo "Create .env.fortimanager with:"
    echo "  FMG_HOST=192.168.1.100"
    echo "  FMG_PASS=your_password"
    echo "  API_URL=https://blacklist.nxtd.co.kr/api/fortinet/active-ips"
    exit 1
fi

source .env.fortimanager

if [[ -z "$FMG_HOST" ]] || [[ -z "$FMG_PASS" ]]; then
    error "FMG_HOST and FMG_PASS required in .env.fortimanager"
    exit 1
fi

log "✅ Prerequisites OK"
log ""

# Step 2: Test connectivity
log "Step 2: Testing connectivity..."

info "  Testing FortiManager ($FMG_HOST)..."
if curl -sk -m 5 "https://$FMG_HOST/jsonrpc" -d '{"method":"get","params":[{"url":"/sys/status"}],"id":1}' >/dev/null 2>&1; then
    log "  ✅ FortiManager reachable"
else
    error "  ❌ Cannot reach FortiManager"
    exit 1
fi

info "  Testing Blacklist API ($API_URL)..."
if curl -sf -m 5 "$API_URL" -o /dev/null; then
    log "  ✅ Blacklist API reachable"
else
    error "  ❌ Cannot reach Blacklist API"
    exit 1
fi

log ""

# Step 3: Initial upload
log "Step 3: Performing initial upload..."

if bash scripts/fortimanager-file-upload.sh; then
    log "✅ Initial upload successful"
else
    error "Initial upload failed"
    exit 1
fi

log ""

# Step 4: Setup cron (5분마다)
log "Step 4: Setting up auto-update (5분마다)..."

CRON_CMD="*/5 * * * * cd $(pwd) && source .env.fortimanager && bash scripts/fortimanager-file-upload.sh >> /var/log/fmg-upload.log 2>&1"

# Check if cron already exists
if crontab -l 2>/dev/null | grep -q "fortimanager-file-upload.sh"; then
    warn "Cron job already exists, skipping..."
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    log "✅ Cron job added"
fi

log ""

# Step 5: FortiManager GUI 설정 안내
log "Step 5: FortiManager GUI 설정..."
echo ""
info "다음 단계를 FortiManager GUI에서 수행하세요:"
echo ""
echo "  1. External Resources 생성"
echo "     - System > External Resources > Create New"
echo "     - Name: NXTD-Blacklist"
echo "     - Type: IP Address"
echo "     - URI: fmg://nxtd-blacklist.txt"
echo "     - Refresh Rate: 5 minutes"
echo "     - Status: Enabled"
echo ""
echo "  2. Policy Package에 적용"
echo "     - Policy & Objects > IPv4 Policy"
echo "     - Source/Destination에 External Resource 추가"
echo ""
echo "  3. FortiGate에 Install Policy"
echo "     - Device Manager > Install"
echo ""

log ""
log "=========================================="
log "✅ Setup Complete"
log "=========================================="
log ""
log "Architecture:"
log "  Blacklist API → FortiManager (5분마다)"
log "  FortiManager → FortiGates (fmg://)"
log ""
log "FortiGate Requirements:"
log "  ✅ 인터넷 연결 불필요"
log "  ✅ FortiManager하고만 통신"
log ""
log "Logs:"
log "  /var/log/fmg-upload.log"
log ""
log "Manual test:"
log "  bash scripts/fortimanager-file-upload.sh"
log ""

exit 0
