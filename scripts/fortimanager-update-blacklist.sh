#!/bin/bash
#
# FortiManager CLI Script Generator for NXTD Blacklist
#
# Purpose:
#   - Flask API에서 블랙리스트 IP 가져오기
#   - FortiManager CLI Script 생성
#   - FortiManager API로 Script 등록 및 실행
#
# Usage:
#   bash fortimanager-update-blacklist.sh
#
# Environment Variables Required:
#   FMG_HOST - FortiManager IP/hostname
#   FMG_USER - FortiManager username (default: admin)
#   FMG_PASS - FortiManager password
#   FMG_ADOM - ADOM name (default: root)
#   API_URL  - Blacklist API URL (default: https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text)

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
FMG_ADOM="${FMG_ADOM:-root}"
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text}"
SCRIPT_NAME="Update-NXTD-Blacklist"
ADDRESS_GROUP_NAME="NXTD-Blacklist-Group"
TMP_DIR="/tmp/fmg-blacklist"
LOG_FILE="/var/log/fortimanager-blacklist-update.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
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

# Create temp directory
mkdir -p "$TMP_DIR"

log "Starting NXTD Blacklist update process..."
log "FortiManager: $FMG_HOST"
log "API URL: $API_URL"

# Step 1: Fetch IP list from API
log "Step 1: Fetching IP list from API..."
IP_FILE="$TMP_DIR/blacklist_ips.txt"

if ! curl -sf "$API_URL" -o "$IP_FILE"; then
    error "Failed to fetch IP list from API"
    exit 1
fi

IP_COUNT=$(wc -l < "$IP_FILE")
log "✅ Fetched $IP_COUNT IPs from API"

if [[ $IP_COUNT -eq 0 ]]; then
    error "No IPs received from API"
    exit 1
fi

# Step 2: Generate FortiManager CLI Script
log "Step 2: Generating FortiManager CLI Script..."
CLI_SCRIPT="$TMP_DIR/fmg_script.txt"

cat > "$CLI_SCRIPT" << 'EOF_HEADER'
config firewall address
EOF_HEADER

# Add each IP as address object
while IFS= read -r ip; do
    # Skip empty lines
    [[ -z "$ip" ]] && continue

    # Convert IP to valid object name (replace . with -)
    name="NXTD-$(echo "$ip" | tr '.' '-')"

    cat >> "$CLI_SCRIPT" << EOF_IP
    edit "$name"
        set type ipmask
        set subnet $ip 255.255.255.255
        set comment "NXTD Blacklist Auto-generated $(date +'%Y-%m-%d')"
    next
EOF_IP
done < "$IP_FILE"

cat >> "$CLI_SCRIPT" << 'EOF_FOOTER'
end

config firewall addrgrp
    edit "NXTD-Blacklist-Group"
        set comment "NXTD Blacklist Address Group - Auto-updated"
        set member
EOF_FOOTER

# Add all addresses to group
while IFS= read -r ip; do
    [[ -z "$ip" ]] && continue
    name="NXTD-$(echo "$ip" | tr '.' '-')"
    echo "            \"$name\"" >> "$CLI_SCRIPT"
done < "$IP_FILE"

cat >> "$CLI_SCRIPT" << 'EOF_END'
    next
end
EOF_END

log "✅ CLI Script generated: $CLI_SCRIPT"
log "Script size: $(wc -l < "$CLI_SCRIPT") lines"

# Step 3: Upload and execute via FortiManager JSON-RPC API
log "Step 3: Uploading script to FortiManager..."

# Login to FortiManager
log "Logging in to FortiManager..."
SESSION_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF_LOGIN
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
EOF_LOGIN
)

SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

if [[ -z "$SESSION_ID" ]]; then
    error "Failed to login to FortiManager"
    error "Response: $SESSION_RESPONSE"
    exit 1
fi

log "✅ Logged in (Session: ${SESSION_ID:0:10}...)"

# Upload CLI Script
log "Uploading CLI script..."
SCRIPT_CONTENT=$(cat "$CLI_SCRIPT" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

UPLOAD_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF_UPLOAD
{
    "method": "set",
    "params": [{
        "url": "/dvmdb/adom/$FMG_ADOM/script",
        "data": {
            "name": "$SCRIPT_NAME",
            "desc": "Auto-update NXTD Blacklist from API",
            "content": "$SCRIPT_CONTENT",
            "type": "cli"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF_UPLOAD
)

UPLOAD_STATUS=$(echo "$UPLOAD_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | cut -d':' -f2)

if [[ "$UPLOAD_STATUS" != "0" ]]; then
    error "Failed to upload script to FortiManager"
    error "Response: $UPLOAD_RESPONSE"

    # Logout
    curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null
    exit 1
fi

log "✅ Script uploaded successfully"

# Execute Script on FortiGates (optional - can be done manually)
warn "⚠️ Script uploaded but NOT executed automatically"
warn "To execute on FortiGates:"
warn "  1. Go to FortiManager GUI > Device Manager > Script"
warn "  2. Select '$SCRIPT_NAME'"
warn "  3. Click 'Run' and select target FortiGates"
warn "  OR use JSON-RPC API to execute programmatically"

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log "✅ Logged out from FortiManager"

# Cleanup
# rm -rf "$TMP_DIR"  # Comment out for debugging

log "="
log "✅ NXTD Blacklist update completed successfully"
log "Summary:"
log "  - Total IPs: $IP_COUNT"
log "  - Script Name: $SCRIPT_NAME"
log "  - Address Group: $ADDRESS_GROUP_NAME"
log "  - Next: Execute script on FortiGates via GUI or API"
log "="

exit 0
