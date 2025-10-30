#!/bin/bash
#
# FortiManager Hosted External Resource Upload
#
# Purpose:
#   - Flask API에서 블랙리스트 다운로드
#   - FortiManager에 파일로 업로드
#   - FortiGate가 FortiManager에서 Pull
#
# Usage:
#   bash fortimanager-hosted-upload.sh

set -euo pipefail

# Configuration
FMG_HOST="${FMG_HOST:-}"
FMG_USER="${FMG_USER:-admin}"
FMG_PASS="${FMG_PASS:-}"
API_URL="${API_URL:-https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text}"
RESOURCE_NAME="NXTD-Blacklist-Hosted"
TMP_FILE="/tmp/nxtd-blacklist.txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Validation
[[ -z "$FMG_HOST" ]] && { error "FMG_HOST required"; exit 1; }
[[ -z "$FMG_PASS" ]] && { error "FMG_PASS required"; exit 1; }

log "Downloading blacklist from API..."
if ! curl -sf "$API_URL" -o "$TMP_FILE"; then
    error "Failed to download from API"
    exit 1
fi

IP_COUNT=$(wc -l < "$TMP_FILE")
log "✅ Downloaded $IP_COUNT IPs"

# Login to FortiManager
log "Logging in to FortiManager..."
SESSION=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/login/user\",\"data\":{\"user\":\"$FMG_USER\",\"passwd\":\"$FMG_PASS\"}}],\"id\":1}" \
    | grep -o '"session":"[^"]*"' | cut -d'"' -f4)

[[ -z "$SESSION" ]] && { error "Login failed"; exit 1; }
log "✅ Logged in"

# Upload file
log "Uploading file to FortiManager..."
FILE_CONTENT=$(cat "$TMP_FILE" | base64 -w 0)

UPLOAD=$(curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -H "Content-Type: application/json" \
    -d "{
        \"method\":\"add\",
        \"params\":[{
            \"url\":\"/pm/config/adom/root/obj/system/external-resource\",
            \"data\":{
                \"name\":\"$RESOURCE_NAME\",
                \"type\":\"address\",
                \"category\":193,
                \"resource\":\"data:text/plain;base64,$FILE_CONTENT\",
                \"comments\":\"NXTD Blacklist - Hosted on FortiManager\"
            }
        }],
        \"session\":\"$SESSION\",
        \"id\":2
    }")

# Logout
curl -sk -X POST "https://$FMG_HOST/jsonrpc" \
    -d "{\"method\":\"exec\",\"params\":[{\"url\":\"/sys/logout\"}],\"session\":\"$SESSION\",\"id\":99}" > /dev/null

log "✅ Upload completed"
log "FortiGate will pull from FortiManager (not external API)"
log ""
log "Next steps:"
log "  1. FortiManager GUI > External Resource"
log "  2. Assign to Policy Package"
log "  3. Install to FortiGates"

rm -f "$TMP_FILE"
exit 0
