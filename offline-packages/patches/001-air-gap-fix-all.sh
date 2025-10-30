#!/bin/bash
#
# Air-Gap Environment All-in-One Fix
# Version: 3.0
# Purpose: Comprehensive fix for all air-gap deployment issues
#
# What this fixes:
# 1. HTTPS port configuration (8443 → 443)
# 2. Monitoring scheduler HTTPS URL
# 3. SECUDIUM URL and file paths
# 4. Database migrations (013, 014)
# 5. REGTECH authentication
# 6. Collection interval
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="blacklist-app"
POSTGRES_CONTAINER="blacklist-postgres"
COLLECTOR_CONTAINER="blacklist-collector"
DB_NAME="blacklist"
DB_USER="postgres"

# Logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        INFO)  echo -e "${GREEN}[INFO]${NC} $message" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" ;;
        *)     echo "$message" ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log ERROR "Docker not found"
        exit 1
    fi

    # Check containers
    for container in "$CONTAINER_NAME" "$POSTGRES_CONTAINER" "$COLLECTOR_CONTAINER"; do
        if ! docker ps | grep -q "$container"; then
            log ERROR "Container $container not running"
            exit 1
        fi
    done

    log INFO "Prerequisites check passed"
}

# Detect PostgreSQL password
detect_postgres_password() {
    local password=""

    # Try .env file
    if [[ -f .env ]]; then
        password=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
        if [[ -n "$password" ]]; then
            echo "$password"
            return 0
        fi
    fi

    if [[ -f ../../.env ]]; then
        password=$(grep "^POSTGRES_PASSWORD=" ../../.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
        if [[ -n "$password" ]]; then
            echo "$password"
            return 0
        fi
    fi

    # Default password
    echo "changeme"
}

# Fix 1: HTTPS port configuration
fix_https_port() {
    log INFO "Fix 1: Updating HTTPS port (8443 → 443)..."

    docker exec "$CONTAINER_NAME" bash -c "cat > /tmp/fix_https_port.py << 'PYEOF'
import sys
import re

def fix_https_port(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Replace port 8443 with 443
        patterns = [
            (r'https://blacklist\.nxtd\.co\.kr:8443', 'https://blacklist.nxtd.co.kr'),
            (r'https://[^:]+:8443', 'https://blacklist.nxtd.co.kr'),
            (r'\"8443\"', '\"443\"'),
            (r\"'8443'\", \"'443'\"),
        ]

        modified = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True

        if modified:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f'✓ Fixed: {file_path}')
            return True
        else:
            print(f'⊘ No changes: {file_path}')
            return False
    except Exception as e:
        print(f'✗ Error: {file_path} - {e}')
        return False

# Fix multiple files
files = [
    '/app/collector/config.py',
    '/app/collector/monitoring_scheduler.py',
    '/app/collector/api/secudium_api.py',
]

fixed_count = 0
for file in files:
    if fix_https_port(file):
        fixed_count += 1

print(f'\\nSummary: Fixed {fixed_count}/{len(files)} files')
sys.exit(0 if fixed_count > 0 else 1)
PYEOF

python3 /tmp/fix_https_port.py
"

    if [[ $? -eq 0 ]]; then
        log INFO "✓ HTTPS port fix completed"
    else
        log WARN "HTTPS port fix had warnings (may be already fixed)"
    fi
}

# Fix 2: Monitoring scheduler HTTPS
fix_monitoring_scheduler() {
    log INFO "Fix 2: Fixing monitoring scheduler HTTPS configuration..."

    docker exec "$COLLECTOR_CONTAINER" bash -c "cat > /tmp/fix_scheduler.py << 'PYEOF'
import os
import re

file_path = '/app/collector/monitoring_scheduler.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix HTTPS configuration
    patterns = [
        (r'http://blacklist-app:2542', 'https://blacklist.nxtd.co.kr'),
        (r'http://localhost:2542', 'https://blacklist.nxtd.co.kr'),
        (r'APP_URL\s*=\s*[\"\\']http://[^\"\\']+(2542)?[\"\\']', 'APP_URL = \"https://blacklist.nxtd.co.kr\"'),
    ]

    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print('✓ Monitoring scheduler fixed')
    else:
        print('⊘ No changes needed')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
PYEOF

python3 /tmp/fix_scheduler.py
"

    log INFO "✓ Monitoring scheduler fix completed"
}

# Fix 3: SECUDIUM configuration
fix_secudium_config() {
    log INFO "Fix 3: Fixing SECUDIUM URL and file paths..."

    docker exec "$CONTAINER_NAME" bash -c "cat > /tmp/fix_secudium.py << 'PYEOF'
import re

file_path = '/app/collector/api/secudium_api.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix SECUDIUM URL
    content = re.sub(
        r'https://www\.secudium\.com:8443',
        'https://www.secudium.com',
        content
    )

    # Fix file paths
    content = re.sub(
        r'/downloads/',
        '/app/downloads/',
        content
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print('✓ SECUDIUM configuration fixed')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
PYEOF

python3 /tmp/fix_secudium.py
"

    log INFO "✓ SECUDIUM fix completed"
}

# Fix 4: Database migrations
fix_database_migrations() {
    log INFO "Fix 4: Applying database migrations..."

    export PGPASSWORD=$(detect_postgres_password)

    # Migration 013: Add notify trigger
    log INFO "Applying migration 013 (notify trigger)..."
    docker exec -e PGPASSWORD="$PGPASSWORD" "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'SQLEOF'
-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS notify_blacklist_change ON blacklist_ips;
DROP FUNCTION IF EXISTS notify_blacklist_change();

-- Create notification function
CREATE OR REPLACE FUNCTION notify_blacklist_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('blacklist_updated',
        json_build_object(
            'operation', TG_OP,
            'ip_address', COALESCE(NEW.ip_address, OLD.ip_address),
            'timestamp', NOW()
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER notify_blacklist_change
AFTER INSERT OR UPDATE OR DELETE ON blacklist_ips
FOR EACH ROW EXECUTE FUNCTION notify_blacklist_change();

\echo '✓ Migration 013 applied'
SQLEOF

    # Migration 014: Add source column
    log INFO "Applying migration 014 (source column)..."
    docker exec -e PGPASSWORD="$PGPASSWORD" "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'SQLEOF'
-- Add source column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'blacklist_ips' AND column_name = 'source'
    ) THEN
        ALTER TABLE blacklist_ips ADD COLUMN source VARCHAR(50) DEFAULT 'REGTECH';
        CREATE INDEX IF NOT EXISTS idx_blacklist_source ON blacklist_ips(source);
        \echo '✓ Migration 014 applied'
    ELSE
        \echo '⊘ Migration 014 already applied'
    END IF;
END $$;
SQLEOF

    log INFO "✓ Database migrations completed"
}

# Fix 5: REGTECH authentication
fix_regtech_auth() {
    log INFO "Fix 5: Fixing REGTECH authentication..."

    docker exec "$CONTAINER_NAME" bash -c "cat > /tmp/fix_regtech.py << 'PYEOF'
import re

file_path = '/app/core/services/collection_service.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix REGTECH authentication endpoint
    content = re.sub(
        r'https?://regtech\.fsec\.or\.kr:\d+',
        'https://regtech.fsec.or.kr',
        content
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print('✓ REGTECH authentication fixed')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
PYEOF

python3 /tmp/fix_regtech.py
"

    log INFO "✓ REGTECH authentication fix completed"
}

# Fix 6: Collection interval
fix_collection_interval() {
    log INFO "Fix 6: Fixing collection interval..."

    docker exec "$COLLECTOR_CONTAINER" bash -c "cat > /tmp/fix_interval.py << 'PYEOF'
import re

file_path = '/app/collector/config.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix collection interval (ensure reasonable value)
    if 'COLLECTION_INTERVAL' in content:
        content = re.sub(
            r'COLLECTION_INTERVAL\s*=\s*\d+',
            'COLLECTION_INTERVAL = 3600',  # 1 hour
            content
        )
    else:
        # Add if not exists
        content += '\n# Collection interval (seconds)\nCOLLECTION_INTERVAL = 3600\n'

    with open(file_path, 'w') as f:
        f.write(content)

    print('✓ Collection interval fixed')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
PYEOF

python3 /tmp/fix_interval.py
"

    log INFO "✓ Collection interval fix completed"
}

# Restart services
restart_services() {
    log INFO "Restarting services..."

    docker restart "$CONTAINER_NAME" "$COLLECTOR_CONTAINER"
    sleep 10

    # Wait for health checks
    local max_wait=60
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if docker exec "$CONTAINER_NAME" curl -sf http://localhost:2542/health > /dev/null 2>&1; then
            log INFO "✓ Services restarted successfully"
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done

    log WARN "Services restarted but health check timeout"
}

# Verify fixes
verify_fixes() {
    log INFO "Verifying fixes..."

    local checks_passed=0
    local checks_total=6

    # Check 1: Containers running
    if docker ps | grep -q "$CONTAINER_NAME"; then
        log INFO "✓ App container running"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ App container not running"
    fi

    # Check 2: Database connection
    export PGPASSWORD=$(detect_postgres_password)
    if docker exec -e PGPASSWORD="$PGPASSWORD" "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log INFO "✓ Database connection OK"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ Database connection failed"
    fi

    # Check 3: API health
    if docker exec "$CONTAINER_NAME" curl -sf http://localhost:2542/health > /dev/null 2>&1; then
        log INFO "✓ API health check passed"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ API health check failed"
    fi

    # Check 4: Migration 013 (notify trigger)
    if docker exec -e PGPASSWORD="$PGPASSWORD" "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_trigger WHERE tgname='notify_blacklist_change'" | grep -q 1; then
        log INFO "✓ Migration 013 (notify trigger) applied"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ Migration 013 not applied"
    fi

    # Check 5: Migration 014 (source column)
    if docker exec -e PGPASSWORD="$PGPASSWORD" "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM information_schema.columns WHERE table_name='blacklist_ips' AND column_name='source'" | grep -q 1; then
        log INFO "✓ Migration 014 (source column) applied"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ Migration 014 not applied"
    fi

    # Check 6: HTTPS configuration
    if docker exec "$CONTAINER_NAME" grep -q "https://blacklist.nxtd.co.kr" /app/collector/config.py 2>/dev/null; then
        log INFO "✓ HTTPS configuration correct"
        checks_passed=$((checks_passed + 1))
    else
        log ERROR "✗ HTTPS configuration incorrect"
    fi

    echo ""
    log INFO "Verification: $checks_passed/$checks_total checks passed"

    return $((checks_total - checks_passed))
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "  Air-Gap Environment All-in-One Fix v3.0"
    echo "=========================================="
    echo ""

    check_prerequisites

    log INFO "Starting comprehensive fix..."
    echo ""

    # Execute all fixes
    fix_https_port
    fix_monitoring_scheduler
    fix_secudium_config
    fix_database_migrations
    fix_regtech_auth
    fix_collection_interval

    # Restart services
    restart_services

    # Verify
    echo ""
    verify_fixes

    echo ""
    log INFO "All-in-one fix completed!"
    echo ""
    log INFO "Next steps:"
    log INFO "  1. Test collection: curl -X POST http://localhost:2542/api/collection/regtech/trigger"
    log INFO "  2. Check logs: docker logs blacklist-app"
    log INFO "  3. Access UI: https://blacklist.nxtd.co.kr"
    echo ""
}

main "$@"
