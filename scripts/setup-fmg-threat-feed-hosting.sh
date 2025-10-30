#!/bin/bash
#
# FortiManager Threat Feed Hosting (중앙 집중식)
#
# Purpose:
#   - FortiManager만 Blacklist API와 통신
#   - FortiManager가 Threat Feed 캐싱
#   - 모든 FortiGate는 FortiManager에서만 가져감
#   - FortiGate 인터넷 접근 불필요
#
# Requirements:
#   - FortiManager 7.4.1+ (Threat Feed Hosting feature)
#
# Usage:
#   bash setup-fmg-threat-feed-hosting.sh

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
FMG_ADOM="${FMG_ADOM:-root}"
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/active-ips}"
CONNECTOR_NAME="NXTD-Blacklist-Hosted"
REFRESH_RATE=5  # 5분

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
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

log "Starting FortiManager Threat Feed Hosting setup..."
log "FortiManager: $FMG_HOST"
log "API URL: $API_URL (FortiManager만 접근)"
log "Connector Name: $CONNECTOR_NAME"

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

# Step 2: Create Threat Feed Connector (Hosted by FortiManager)
log "Step 2: Creating Threat Feed Connector (FortiManager hosts)..."
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
            "comments": "NXTD Blacklist - Hosted by FortiManager (FortiGates pull from FMG)",
            "server-identity-check": "none"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

CREATE_CODE=$(echo "$CREATE_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$CREATE_CODE" == "0" ]]; then
    log "✅ Threat Feed Connector created (FortiManager Hosted)"
elif [[ "$CREATE_CODE" == "-2" ]]; then
    warn "⚠️ Connector already exists, updating..."
    # Update existing
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
    log "✅ Connector updated"
else
    error "Failed to create Threat Feed Connector"
    error "Response: $CREATE_RESPONSE"
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

# Step 3: Configure FortiManager to cache/host the feed
log "Step 3: Configuring FortiManager as Threat Feed Host..."
HOST_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/cli/global/system/connector",
        "data": {
            "name": "$CONNECTOR_NAME",
            "type": "threat-feed",
            "server": "$API_URL",
            "refresh-rate": $REFRESH_RATE,
            "status": "enable"
        }
    }],
    "session": "$SESSION_ID",
    "id": 4
}
EOF
)

HOST_CODE=$(echo "$HOST_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$HOST_CODE" == "0" ]] || [[ "$HOST_CODE" == "-2" ]]; then
    log "✅ FortiManager configured as Threat Feed Host"
else
    warn "⚠️ Threat Feed Hosting requires FortiManager 7.4.1+"
    info "Falling back to standard External Connector mode"
fi

# Step 4: Create Firewall Address Group
log "Step 4: Creating Firewall Address Group..."
GROUP_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "set",
    "params": [{
        "url": "/pm/config/adom/$FMG_ADOM/obj/firewall/addrgrp",
        "data": {
            "name": "NXTD-Blacklist-Group",
            "member": ["$CONNECTOR_NAME"],
            "comment": "NXTD Blacklist - Auto-updated from FortiManager"
        }
    }],
    "session": "$SESSION_ID",
    "id": 5
}
EOF
)

GROUP_CODE=$(echo "$GROUP_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$GROUP_CODE" == "0" ]]; then
    log "✅ Address Group created"
elif [[ "$GROUP_CODE" == "-2" ]]; then
    info "Address Group already exists (OK)"
fi

# Step 5: Create Sample Firewall Policy
log "Step 5: Creating sample firewall policy..."
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
            "srcaddr": ["NXTD-Blacklist-Group"],
            "dstaddr": ["all"],
            "action": "deny",
            "schedule": "always",
            "service": ["ALL"],
            "logtraffic": "all",
            "comments": "Auto-block NXTD Blacklist IPs (via FortiManager)"
        }
    }],
    "session": "$SESSION_ID",
    "id": 6
}
EOF
)

POLICY_CODE=$(echo "$POLICY_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$POLICY_CODE" == "0" ]]; then
    log "✅ Sample policy created"
elif [[ "$POLICY_CODE" == "-2" ]]; then
    info "Policy already exists (OK)"
fi

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log ""
log "=========================================="
log "✅ FortiManager Threat Feed Hosting Setup Complete"
log "=========================================="
log ""
log "Architecture:"
log "  1. FortiManager pulls from: $API_URL"
log "  2. FortiManager caches IPs locally"
log "  3. FortiGates pull from FortiManager (no internet needed)"
log ""
log "Configuration:"
log "  - Connector: $CONNECTOR_NAME"
log "  - Refresh Rate: ${REFRESH_RATE} minutes"
log "  - Address Group: NXTD-Blacklist-Group"
log "  - Policy: Block-NXTD-Blacklist"
log ""
log "Network Requirements:"
log "  ✅ FortiManager → Internet (API access)"
log "  ❌ FortiGate → Internet (NOT required)"
log "  ✅ FortiGate → FortiManager (internal only)"
log ""
log "Next Steps:"
log "  1. Install Policy Package to all FortiGates:"
log "     bash scripts/install-fmg-policy-to-all-devices.sh"
log ""
log "  2. Enable Auto-Install (optional):"
log "     bash scripts/enable-fmg-auto-install.sh"
log ""
log "Verification (FortiGate CLI):"
log "  # FortiGates should pull from FortiManager, not API"
log "  diagnose sys external-resource list"
log "  diagnose firewall address-list list $CONNECTOR_NAME"
log ""

exit 0
