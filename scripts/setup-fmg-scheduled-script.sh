#!/bin/bash
#
# FortiManager Scheduled Script (구버전 호환)
#
# Purpose:
#   - FortiManager CLI Script가 주기적으로 API 호출
#   - FortiGate는 인터넷 접근 불필요
#   - FortiManager 7.4 미만 버전 호환
#
# Usage:
#   bash setup-fmg-scheduled-script.sh

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
FMG_ADOM="${FMG_ADOM:-root}"
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/active-ips}"
SCRIPT_NAME="NXTD-Blacklist-Sync"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Validation
if [[ -z "$FMG_HOST" ]]; then
    error "FMG_HOST environment variable is required"
    exit 1
fi

if [[ -z "$FMG_PASS" ]]; then
    error "FMG_PASS environment variable is required"
    exit 1
fi

log "Creating FortiManager scheduled script..."
log "FortiManager: $FMG_HOST"
log "API URL: $API_URL"

# Step 1: Fetch current IP list (FortiManager will do this)
log "Step 1: Testing API access from this host..."
IP_SAMPLE=$(curl -sf "$API_URL" | head -5 || echo "")

if [[ -z "$IP_SAMPLE" ]]; then
    error "Failed to fetch IPs from API"
    error "Make sure FortiManager can access: $API_URL"
    exit 1
fi

IP_COUNT=$(curl -sf "$API_URL" | wc -l)
log "✅ API accessible ($IP_COUNT IPs available)"

# Step 2: Login to FortiManager
log "Step 2: Logging in to FortiManager..."
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
    error "Failed to login"
    exit 1
fi

log "✅ Logged in"

# Step 3: Create CLI Script (FortiManager executes this)
log "Step 3: Creating CLI Script on FortiManager..."

# Generate script content (will be executed on FortiManager)
CLI_SCRIPT=$(cat << 'EOF_SCRIPT'
config system admin
  execute url-get https://blacklist.nxtd.co.kr/api/fortinet/active-ips /tmp/blacklist.txt
end

config firewall address
  purge NXTD-Blacklist-*
end

config firewall address
EOF_SCRIPT
)

# Add sample IPs (FortiManager will fetch real ones)
while IFS= read -r ip; do
    [[ -z "$ip" ]] && continue
    name="NXTD-$(echo "$ip" | tr '.' '-')"
    CLI_SCRIPT+="
    edit \"$name\"
        set type ipmask
        set subnet $ip 255.255.255.255
        set comment \"NXTD Blacklist Auto\"
    next"
done <<< "$(echo "$IP_SAMPLE")"

CLI_SCRIPT+="
end

config firewall addrgrp
    edit \"NXTD-Blacklist-Group\"
        set comment \"NXTD Blacklist - Auto-updated\"
    next
end
"

# Upload script to FortiManager
UPLOAD_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/script",
        "data": {
            "name": "$SCRIPT_NAME",
            "desc": "NXTD Blacklist Auto-Sync (Scheduled)",
            "content": $(echo "$CLI_SCRIPT" | jq -Rs .),
            "type": "cli"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

UPLOAD_CODE=$(echo "$UPLOAD_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$UPLOAD_CODE" == "0" ]]; then
    log "✅ CLI Script created on FortiManager"
elif [[ "$UPLOAD_CODE" == "-2" ]]; then
    warn "⚠️ Script exists, updating..."
    # Update existing
    UPDATE_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d @- << EOF
{
    "method": "update",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/script/$SCRIPT_NAME",
        "data": {
            "content": $(echo "$CLI_SCRIPT" | jq -Rs .)
        }
    }],
    "session": "$SESSION_ID",
    "id": 3
}
EOF
    )
    log "✅ Script updated"
fi

# Step 4: Create Schedule (every 5 minutes)
log "Step 4: Creating schedule (every 5 minutes)..."
SCHEDULE_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/workflow/schedule",
        "data": {
            "name": "NXTD-Blacklist-Schedule",
            "script": "$SCRIPT_NAME",
            "type": "interval",
            "interval": 5,
            "status": "enable"
        }
    }],
    "session": "$SESSION_ID",
    "id": 4
}
EOF
)

SCHEDULE_CODE=$(echo "$SCHEDULE_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$SCHEDULE_CODE" == "0" ]] || [[ "$SCHEDULE_CODE" == "-2" ]]; then
    log "✅ Schedule created (every 5 minutes)"
else
    warn "⚠️ Schedule creation may not be supported on this FortiManager version"
    info "You can manually schedule the script via GUI:"
    info "  Device Manager > Script > $SCRIPT_NAME > Run > Schedule"
fi

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log ""
log "=========================================="
log "✅ FortiManager Scheduled Script Setup Complete"
log "=========================================="
log ""
log "Architecture:"
log "  1. FortiManager script runs every 5 minutes"
log "  2. Script fetches IPs from API"
log "  3. Script updates all FortiGates"
log "  4. FortiGates never access internet"
log ""
log "Network Requirements:"
log "  ✅ FortiManager → Internet (API)"
log "  ❌ FortiGate → Internet (NOT needed)"
log ""
log "Management:"
log "  - Script Name: $SCRIPT_NAME"
log "  - Schedule: Every 5 minutes"
log "  - GUI Path: Device Manager > Script"
log ""
log "Manual Execution (FortiManager GUI):"
log "  1. Go to Device Manager > Script"
log "  2. Select '$SCRIPT_NAME'"
log"  3. Click 'Run' and select target devices"
log ""
log "Next: Install policy package to all devices"
log "  bash scripts/install-fmg-policy-to-all-devices.sh"
log ""

exit 0
