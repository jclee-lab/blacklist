#!/bin/bash
#
# FortiManager Policy Package Auto-Install to All Devices
#
# Purpose:
#   - Policy Package를 모든 FortiGate에 자동 설치
#   - 실시간 연동을 위한 Auto-Install 설정
#
# Usage:
#   bash install-fmg-policy-to-all-devices.sh
#
# Environment Variables:
#   FMG_HOST - FortiManager IP/hostname
#   FMG_USER - FortiManager username (default: admin)
#   FMG_PASS - FortiManager password
#   FMG_ADOM - ADOM name (default: root)
#   POLICY_PKG - Policy Package name (default: default)

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
FMG_ADOM="${FMG_ADOM:-root}"
POLICY_PKG="${POLICY_PKG:-default}"

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

log "Starting Policy Package installation to all devices..."
log "FortiManager: $FMG_HOST"
log "ADOM: $FMG_ADOM"
log "Policy Package: $POLICY_PKG"

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
    error "Response: $SESSION_RESPONSE"
    exit 1
fi

log "✅ Logged in (Session: ${SESSION_ID:0:10}...)"

# Step 2: Get all managed devices
log "Step 2: Retrieving all managed devices..."
DEVICES_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "get",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/device"
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

# Extract device names
DEVICE_NAMES=$(echo "$DEVICES_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
DEVICE_COUNT=$(echo "$DEVICE_NAMES" | wc -l)

if [[ -z "$DEVICE_NAMES" ]]; then
    error "No devices found in ADOM: $FMG_ADOM"
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

log "✅ Found $DEVICE_COUNT devices:"
echo "$DEVICE_NAMES" | while read -r device; do
    info "  - $device"
done

# Step 3: Install policy to all devices
log "Step 3: Installing policy package to all devices..."

# Build scope list
SCOPE_LIST=""
for device in $DEVICE_NAMES; do
    if [[ -n "$SCOPE_LIST" ]]; then
        SCOPE_LIST="$SCOPE_LIST,"
    fi
    SCOPE_LIST="$SCOPE_LIST{\"name\":\"$device\",\"vdom\":\"root\"}"
done

# Install policy
INSTALL_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "exec",
    "params": [{
        "url": "/securityconsole/install/package",
        "data": {
            "adom": "$FMG_ADOM",
            "pkg": "$POLICY_PKG",
            "scope": [$SCOPE_LIST],
            "flags": ["none"]
        }
    }],
    "session": "$SESSION_ID",
    "id": 3
}
EOF
)

TASK_ID=$(echo "$INSTALL_RESPONSE" | grep -o '"task":[0-9]*' | cut -d':' -f2)

if [[ -z "$TASK_ID" ]]; then
    error "Failed to start policy installation"
    error "Response: $INSTALL_RESPONSE"
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

log "✅ Policy installation started (Task ID: $TASK_ID)"

# Step 4: Monitor installation progress
log "Step 4: Monitoring installation progress..."
for i in {1..60}; do
    sleep 2
    STATUS_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d @- << EOF
{
    "method": "get",
    "params": [{
        "url": "/task/task/$TASK_ID"
    }],
    "session": "$SESSION_ID",
    "id": 4
}
EOF
    )

    PERCENT=$(echo "$STATUS_RESPONSE" | grep -o '"percent":[0-9]*' | cut -d':' -f2)
    STATE=$(echo "$STATUS_RESPONSE" | grep -o '"state":[0-9]*' | cut -d':' -f2)

    if [[ "$STATE" == "1" ]]; then
        log "✅ Installation completed successfully (100%)"
        break
    elif [[ "$STATE" == "2" ]]; then
        error "Installation failed"
        error "Response: $STATUS_RESPONSE"
        break
    else
        info "Progress: ${PERCENT:-0}%"
    fi

    if [[ $i -eq 60 ]]; then
        warn "⚠️ Installation timeout (2 minutes)"
    fi
done

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log "✅ Logged out from FortiManager"

log ""
log "=========================================="
log "✅ Policy Package Installation Complete"
log "=========================================="
log ""
log "Summary:"
log "  - Devices: $DEVICE_COUNT"
log "  - Policy Package: $POLICY_PKG"
log "  - Task ID: $TASK_ID"
log ""
log "Next: Enable Auto-Install for real-time updates"
log "Run: bash enable-fmg-auto-install.sh"
log ""

exit 0
