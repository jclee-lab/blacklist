#!/bin/bash
#
# FortiManager File Upload for Threat Feed Hosting
#
# Purpose:
#   1. Download blacklist from API
#   2. Upload to FortiManager (file-based hosting)
#   3. FortiGate pulls from FortiManager (fmg://blacklist.txt)
#
# Requirements:
#   - FortiManager 7.4.1+
#   - Cron for auto-update
#
# Usage:
#   bash fortimanager-file-upload.sh

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/active-ips}"
FILENAME="nxtd-blacklist.txt"
TMP_FILE="/tmp/$FILENAME"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Validation
if [[ -z "$FMG_HOST" ]] || [[ -z "$FMG_PASS" ]]; then
    error "FMG_HOST and FMG_PASS required"
    echo "Usage: FMG_HOST=192.168.1.10 FMG_PASS=password bash $0"
    exit 1
fi

log "Starting FortiManager File Upload..."

# Step 1: Download from API
log "Step 1: Downloading blacklist from API..."
if curl -sf "$API_URL" -o "$TMP_FILE"; then
    IP_COUNT=$(wc -l < "$TMP_FILE")
    log "✅ Downloaded $IP_COUNT IPs"
else
    error "Failed to download from API"
    exit 1
fi

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

# Step 3: Upload file to FortiManager
log "Step 3: Uploading file to FortiManager..."

# Base64 encode file content
FILE_CONTENT=$(base64 -w 0 "$TMP_FILE")

UPLOAD_RESPONSE=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d @- << EOF
{
    "method": "add",
    "params": [{
        "url": "/pm/config/adom/root/obj/system/external-resource",
        "data": {
            "name": "$FILENAME",
            "type": "address",
            "resource": "fmg://$FILENAME",
            "status": "enable",
            "comments": "NXTD Blacklist - File hosted on FortiManager"
        }
    }],
    "session": "$SESSION_ID",
    "id": 2
}
EOF
)

UPLOAD_CODE=$(echo "$UPLOAD_RESPONSE" | grep -o '"code":[0-9-]*' | head -1 | cut -d':' -f2)

if [[ "$UPLOAD_CODE" == "0" ]] || [[ "$UPLOAD_CODE" == "-2" ]]; then
    log "✅ File uploaded/updated"
else
    error "Failed to upload file"
    error "Response: $UPLOAD_RESPONSE"
fi

# Cleanup
rm -f "$TMP_FILE"

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION_ID\",\"id\":99}" > /dev/null

log ""
log "=========================================="
log "✅ FortiManager File Upload Complete"
log "=========================================="
log ""
log "File: fmg://$FILENAME"
log "IPs: $IP_COUNT"
log ""
log "Next: Create Threat Feed in FortiManager GUI"
log "  URI: fmg://$FILENAME"
log ""

exit 0
