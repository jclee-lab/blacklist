#!/bin/bash
#
# Setup Cron Job for FortiManager Blacklist Auto-Update
#
# Usage:
#   bash setup-fortimanager-cron.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/fortimanager-update-blacklist.sh"
ENV_FILE="$SCRIPT_DIR/../.env.fortimanager"

# Create environment file template
cat > "$ENV_FILE" << 'EOF'
# FortiManager Configuration
FMG_HOST=192.168.1.100
FMG_USER=admin
FMG_PASS=your_password_here
FMG_ADOM=root

# API Configuration
API_URL=https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text
EOF

echo "✅ Environment template created: $ENV_FILE"
echo ""
echo "📝 Please edit $ENV_FILE and set correct values:"
echo "   - FMG_HOST: FortiManager IP/hostname"
echo "   - FMG_PASS: FortiManager password"
echo ""
read -p "Press Enter after editing the file..."

# Validate environment file
if ! grep -q "^FMG_HOST=" "$ENV_FILE" || ! grep -q "^FMG_PASS=" "$ENV_FILE"; then
    echo "❌ Environment file not configured properly"
    exit 1
fi

# Create cron wrapper script
CRON_WRAPPER="$SCRIPT_DIR/fortimanager-cron-wrapper.sh"
cat > "$CRON_WRAPPER" << EOF
#!/bin/bash
set -a
source "$ENV_FILE"
set +a
"$CRON_SCRIPT" >> /var/log/fortimanager-blacklist-cron.log 2>&1
EOF

chmod +x "$CRON_WRAPPER"

# Add to crontab (every 10 minutes)
CRON_ENTRY="*/10 * * * * $CRON_WRAPPER"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "$CRON_WRAPPER"; then
    echo "⚠️ Cron job already exists"
    crontab -l | grep "$CRON_WRAPPER"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job added successfully"
    echo ""
    echo "Cron schedule: Every 10 minutes"
    echo "Command: $CRON_WRAPPER"
fi

echo ""
echo "📋 To view logs:"
echo "   tail -f /var/log/fortimanager-blacklist-update.log"
echo "   tail -f /var/log/fortimanager-blacklist-cron.log"
echo ""
echo "📋 To test immediately:"
echo "   bash $CRON_WRAPPER"
echo ""
echo "📋 To remove cron job:"
echo "   crontab -e  # and delete the line with: $CRON_WRAPPER"

exit 0
