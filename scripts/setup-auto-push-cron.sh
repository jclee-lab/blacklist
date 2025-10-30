#!/bin/bash
#
# Setup Cron for Auto-Push to FortiGates
#
# Purpose:
#   - 5분마다 자동으로 모든 FortiGate에 Blacklist Push
#   - FortiManager 불필요
#   - 완전 자동화

set -euo pipefail

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

# Get user input
echo "=========================================="
echo "FortiGate Auto-Push Cron Setup"
echo "=========================================="
echo ""

read -p "FortiGate IPs (comma-separated, e.g., 192.168.1.1,192.168.1.2): " FORTIGATE_HOSTS
read -sp "FortiGate API Token: " FORTIGATE_TOKEN
echo ""

if [[ -z "$FORTIGATE_HOSTS" ]] || [[ -z "$FORTIGATE_TOKEN" ]]; then
    error "Both inputs are required"
    exit 1
fi

# Create environment file
ENV_FILE="/etc/fortigate-push.env"
log "Creating environment file: $ENV_FILE"

sudo bash -c "cat > $ENV_FILE" << EOF
# FortiGate Auto-Push Configuration
FORTIGATE_HOSTS="$FORTIGATE_HOSTS"
FORTIGATE_TOKEN="$FORTIGATE_TOKEN"
BLACKLIST_API="https://blacklist.nxtd.co.kr/api/fortinet/active-ips"
EOF

sudo chmod 600 "$ENV_FILE"
log "✅ Environment file created"

# Create cron job
SCRIPT_PATH="/home/jclee/app/blacklist/scripts/auto-push-to-fortigates.py"
CRON_LINE="*/5 * * * * source $ENV_FILE && /usr/bin/python3 $SCRIPT_PATH >> /var/log/fortigate-push.log 2>&1"

log "Adding cron job..."
(crontab -l 2>/dev/null | grep -v "auto-push-to-fortigates.py"; echo "$CRON_LINE") | crontab -

log "✅ Cron job added"

# Create log file
sudo touch /var/log/fortigate-push.log
sudo chmod 644 /var/log/fortigate-push.log

log "✅ Log file created: /var/log/fortigate-push.log"

# Test run
log "Testing initial push..."
source "$ENV_FILE"
python3 "$SCRIPT_PATH"

log ""
log "=========================================="
log "✅ Auto-Push Cron Setup Complete"
log "=========================================="
log ""
log "Configuration:"
log "  - FortiGates: $FORTIGATE_HOSTS"
log "  - Schedule: Every 5 minutes"
log "  - Log: /var/log/fortigate-push.log"
log ""
log "Monitoring:"
log "  tail -f /var/log/fortigate-push.log"
log ""
log "Manual trigger:"
log "  source $ENV_FILE && python3 $SCRIPT_PATH"
log ""

exit 0
