#!/bin/bash
#
# FortiManager External Connector Setup
#
# Purpose:
#   - FortiManager에 External Connector 등록
#   - Blacklist API를 주기적으로 Pull
#   - Policy Package로 모든 FortiGate에 자동 배포
#
# Usage:
#   bash setup-fmg-external-connector.sh
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
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/active-ips}"
CONNECTOR_NAME="NXTD-Blacklist-Feed"
REFRESH_RATE=5  # 5분마다 갱신

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
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
    echo "Usage: FMG_HOST=192.168.1.10 FMG_PASS=password bash $0"
    exit 1
fi

if [[ -z "$FMG_PASS" ]]; then
    error "FMG_PASS environment variable is required"
    exit 1
fi

log "Starting FortiManager External Connector setup..."
log "FortiManager: $FMG_HOST"
log "API URL: $API_URL"
log "Connector Name: $CONNECTOR_NAME"

# Step 1: Login to FortiManager
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

# Step 2: Create External Connector (Threat Feed)
log "Step 2: Creating External Connector..."
CREATE_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/pm/config/adom/$FMG_ADOM/obj/system/external-resource",
        "data": {
            "name": "$CONNECTOR_NAME",
            "type": "address",
            "category": 189,
            "resource": "$API_URL",
            "refresh-rate": $REFRESH_RATE,
            "status": "enable",
            "comments": "NXTD Blacklist API - Auto-sync every ${REFRESH_RATE}min"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

CREATE_CODE=$(echo "$CREATE_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

if [[ "$CREATE_CODE" == "0" ]]; then
    log "✅ External Connector created successfully"
elif [[ "$CREATE_CODE" == "-2" ]]; then
    warn "⚠️ External Connector already exists, updating..."

    # Update existing connector
    UPDATE_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d @- << EOF
{
    "method": "update",
    "params": [{
        "url": "/pm/config/adom/$FMG_ADOM/obj/system/external-resource/$CONNECTOR_NAME",
        "data": {
            "resource": "$API_URL",
            "refresh-rate": $REFRESH_RATE,
            "status": "enable"
        }
    }],
    "session": "$SESSION_ID",
    "id": 3
}
EOF
    )
    log "✅ External Connector updated"
else
    error "Failed to create External Connector"
    error "Response: $CREATE_RESPONSE"
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

# Step 3: Create Firewall Policy (Optional - 예시)
log "Step 3: Creating sample firewall policy..."
POLICY_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "add",
    "params": [{
        "url": "/pm/config/adom/$FMG_ADOM/pkg/default/firewall/policy",
        "data": {
            "name": "Block-NXTD-Blacklist",
            "srcintf": ["any"],
            "dstintf": ["any"],
            "srcaddr": ["$CONNECTOR_NAME"],
            "dstaddr": ["all"],
            "action": "deny",
            "schedule": "always",
            "service": ["ALL"],
            "logtraffic": "all",
            "comments": "Auto-block NXTD Blacklist IPs"
        }
    }],
    "session": "$SESSION_ID",
    "id": 4
}
EOF
)

POLICY_CODE=$(echo "$POLICY_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

if [[ "$POLICY_CODE" == "0" ]]; then
    log "✅ Sample policy created"
elif [[ "$POLICY_CODE" == "-2" ]]; then
    warn "⚠️ Policy already exists (skipping)"
else
    warn "⚠️ Failed to create policy (you can create manually)"
fi

# Step 4: Install Policy Package to FortiGates
log "Step 4: Preparing policy installation..."
warn "⚠️ Policy installation must be done via GUI or separate script"
warn "To install policy package:"
warn "  1. Go to FortiManager GUI > Policy & Objects"
warn "  2. Select Policy Package > Install"
warn "  3. Select target FortiGates"
warn "  4. Click 'Install'"

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log "✅ Logged out from FortiManager"

log ""
log "=========================================="
log "✅ FortiManager External Connector Setup Complete"
log "=========================================="
log ""
log "Configuration Summary:"
log "  - Connector Name: $CONNECTOR_NAME"
log "  - API URL: $API_URL"
log "  - Refresh Rate: ${REFRESH_RATE} minutes"
log "  - Status: Enabled"
log ""
log "Next Steps:"
log "  1. Install Policy Package to all FortiGates"
log "  2. Enable Auto-Install for real-time updates"
log "  3. Monitor External Connector status"
log ""
log "Verification Commands (FortiGate CLI):"
log "  diagnose sys external-resource list"
log "  diagnose firewall address-list list $CONNECTOR_NAME"
log ""

exit 0
