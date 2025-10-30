#!/bin/bash
#
# Direct FortiGate Threat Feed Push
#
# Purpose:
#   - FortiManager 없이 각 FortiGate에 직접 푸시
#   - 7.4.1 미만 버전에서 사용 가능
#
# Requirements:
#   - FortiGate 6.0+
#   - FortiGate API access
#
# Usage:
#   bash push-to-fortigates.sh

set -euo pipefail

# Configuration
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/active-ips}"
RESOURCE_NAME="${RESOURCE_NAME:-NXTD-Blacklist}"
TMP_FILE="/tmp/nxtd-blacklist.txt"

# FortiGate list (comma-separated)
# Format: "host:port:token,host:port:token"
FORTIGATE_LIST="${FORTIGATE_LIST:-}"

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

# Validation
if [[ -z "$FORTIGATE_LIST" ]]; then
    error "FORTIGATE_LIST required"
    echo ""
    echo "Usage:"
    echo "  FORTIGATE_LIST='192.168.1.10:443:token1,192.168.1.20:443:token2' bash $0"
    echo ""
    echo "Environment Variables:"
    echo "  FORTIGATE_LIST   - Comma-separated list (host:port:token)"
    echo "  API_URL          - Blacklist API URL (default: https://blacklist.nxtd.co.kr/api/fortinet/active-ips)"
    echo "  RESOURCE_NAME    - External resource name (default: NXTD-Blacklist)"
    echo ""
    exit 1
fi

log "Starting FortiGate Direct Push..."
log "API: $API_URL"
log "Resource: $RESOURCE_NAME"
log ""

# Step 1: Download blacklist
log "Step 1: Downloading blacklist from API..."
if ! curl -sf "$API_URL" -o "$TMP_FILE"; then
    error "Failed to download from API"
    exit 1
fi

IP_COUNT=$(wc -l < "$TMP_FILE")
log "✅ Downloaded $IP_COUNT IPs"
log ""

# Step 2: Push to each FortiGate
IFS=',' read -ra FG_ARRAY <<< "$FORTIGATE_LIST"
TOTAL=${#FG_ARRAY[@]}
SUCCESS=0
FAILED=0

log "Step 2: Pushing to $TOTAL FortiGate(s)..."
log ""

for FG_INFO in "${FG_ARRAY[@]}"; do
    IFS=':' read -r FG_HOST FG_PORT FG_TOKEN <<< "$FG_INFO"

    info "Processing $FG_HOST:$FG_PORT..."

    # Method 1: REST API Push (FortiOS 6.2+)
    RESPONSE=$(curl -sk -X POST "https://$FG_HOST:$FG_PORT/api/v2/cmdb/system/external-resource" \
        -H "Authorization: Bearer $FG_TOKEN" \
        -H "Content-Type: application/json" \
        -d @- 2>/dev/null << EOF || echo "ERROR"
{
    "name": "$RESOURCE_NAME",
    "type": "address",
    "category": 193,
    "resource": "data:text/plain;base64,$(base64 -w 0 "$TMP_FILE")",
    "comments": "NXTD Blacklist - Direct Push",
    "status": "enable"
}
EOF
    )

    if [[ "$RESPONSE" == "ERROR" ]] || echo "$RESPONSE" | grep -q '"status":"error"'; then
        # Method 2: Try Push Method (FortiOS 7.0+)
        warn "  API method failed, trying push method..."

        PUSH_RESPONSE=$(curl -sk -X PUT "https://$FG_HOST:$FG_PORT/api/v2/cmdb/system/external-resource/$RESOURCE_NAME" \
            -H "Authorization: Bearer $FG_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"update-method\":\"push\",\"category\":193}" 2>/dev/null || echo "ERROR")

        if [[ "$PUSH_RESPONSE" != "ERROR" ]] && ! echo "$PUSH_RESPONSE" | grep -q '"status":"error"'; then
            # Push content
            curl -sk -X POST "https://$FG_HOST:$FG_PORT/api/v2/monitor/system/external-resource/push?mkey=$RESOURCE_NAME" \
                -H "Authorization: Bearer $FG_TOKEN" \
                --data-binary "@$TMP_FILE" >/dev/null 2>&1

            log "  ✅ Pushed to $FG_HOST (push method)"
            ((SUCCESS++))
        else
            error "  ❌ Failed to push to $FG_HOST"
            ((FAILED++))
        fi
    else
        log "  ✅ Pushed to $FG_HOST (API method)"
        ((SUCCESS++))
    fi

    sleep 0.5
done

# Cleanup
rm -f "$TMP_FILE"

log ""
log "=========================================="
log "✅ FortiGate Direct Push Complete"
log "=========================================="
log ""
log "Results: $SUCCESS/$TOTAL successful, $FAILED failed"
log "IPs: $IP_COUNT"
log ""

if [[ $FAILED -gt 0 ]]; then
    warn "Some FortiGates failed. Check logs above."
    exit 1
fi

exit 0
