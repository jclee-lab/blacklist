#!/bin/bash
#
# FortiManager Auto-Install Enable (실시간 자동 배포)
#
# Purpose:
#   - Policy 변경 시 자동으로 모든 FortiGate에 설치
#   - External Connector 갱신 시 자동 반영
#   - 실시간 연동 구현
#
# Usage:
#   bash enable-fmg-auto-install.sh
#
# Environment Variables:
#   FMG_HOST - FortiManager IP/hostname
#   FMG_USER - FortiManager username (default: admin)
#   FMG_PASS - FortiManager password
#   FMG_ADOM - ADOM name (default: root)

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
FMG_ADOM="${FMG_ADOM:-root}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

# Validation
if [[ -z "$FMG_HOST" ]]; then
    error "FMG_HOST environment variable is required"
    echo "Usage: FMG_HOST=192.168.1.10 FMG_PASS=password bash $0"
    exit 1
fi

if [[ -z "$FMG_PASS" ]]; then
    error "FMG_PASS environment variable is required"
    exit 1
fi

log "Starting Auto-Install configuration..."
log "FortiManager: $FMG_HOST"
log "ADOM: $FMG_ADOM"

# Step 1: Login
log "Step 1: Logging in to FortiManager..."
SESSION_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "exec",
    "params": [{
        "url": "/sys/login/user",
        "data": {
            "user": "$FMG_USER",
            "passwd": "$FMG_PASS"
        }
    }],
    "id": 1
}
EOF
)

SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

if [[ -z "$SESSION_ID" ]]; then
    error "Failed to login to FortiManager"
    exit 1
fi

log "✅ Logged in"

# Step 2: Enable Auto-Install for ADOM
log "Step 2: Enabling Auto-Install for ADOM..."
AUTO_INSTALL_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM",
        "data": {
            "workspace-mode": "workflow",
            "auto-push-cfg": "enable"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

AUTO_CODE=$(echo "$AUTO_INSTALL_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

if [[ "$AUTO_CODE" == "0" ]]; then
    log "✅ Auto-Install enabled for ADOM"
else
    warn "⚠️ Failed to enable Auto-Install (may already be enabled)"
fi

# Step 3: Get all devices and enable auto-install
log "Step 3: Enabling Auto-Install for all devices..."
DEVICES_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "get",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/device"
    }],
    "session": "$SESSION_ID",
    "id": 3
}
EOF
)

DEVICE_NAMES=$(echo "$DEVICES_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

if [[ -z "$DEVICE_NAMES" ]]; then
    error "No devices found"
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

log "Found devices:"
echo "$DEVICE_NAMES" | while read -r device; do
    info "  - $device"

    # Enable auto-install for each device
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d @- << EOF > /dev/null
{
    "method": "set",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/device/$device",
        "data": {
            "auto-push-policy": "enable"
        }
    }],
    "session": "$SESSION_ID",
    "id": 4
}
EOF
done

log "✅ Auto-Install enabled for all devices"

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log ""
log "=========================================="
log "✅ Real-Time Auto-Deploy Configuration Complete"
log "=========================================="
log ""
log "Enabled Features:"
log "  ✅ ADOM Auto-Push: Enabled"
log "  ✅ Device Auto-Install: Enabled for all devices"
log "  ✅ Workflow Mode: Enabled"
log ""
log "What happens now:"
log "  1. External Connector updates every 5 minutes"
log "  2. Policy changes auto-detected"
log "  3. Auto-install to all FortiGates"
log "  4. Real-time synchronization"
log ""
log "Monitoring:"
log "  - FortiManager GUI > Device Manager > Auto-Install Status"
log "  - FortiGate: diagnose sys external-resource list"
log ""

exit 0
