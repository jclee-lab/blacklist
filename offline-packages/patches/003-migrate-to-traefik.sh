#!/bin/bash
#
# Patch 002: Migrate to Traefik Reverse Proxy
# ==============================================
#
# Problem:
# 1. nginx 기반 배포에서 Traefik 기반으로 전환 필요
# 2. HTTPS-only (443 포트) 설정으로 간소화
# 3. Traefik labels 최적화 (15+ lines → 6 lines)
#
# Solution:
# 1. docker-compose.yml에 Traefik 설정 추가
# 2. blacklist-frontend에 traefik-public 네트워크 연결
# 3. HTTPS-only labels 설정 (HTTP redirect 제거)
# 4. nginx 컨테이너 중지 (선택적)
#
# Version: 3.3.8
# Date: 2025-10-30
# Author: Claude Code

set -eo pipefail

# Color codes
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
NC=$'\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Starting Patch 005: Migrate to Traefik"
log_info "========================================"

# Detect docker-compose.yml location
COMPOSE_FILE=""
if [ -f "/app/docker-compose.yml" ]; then
    COMPOSE_FILE="/app/docker-compose.yml"
elif [ -f "/home/jclee/app/blacklist/docker-compose.yml" ]; then
    COMPOSE_FILE="/home/jclee/app/blacklist/docker-compose.yml"
elif [ -f "./docker-compose.yml" ]; then
    COMPOSE_FILE="./docker-compose.yml"
else
    log_error "docker-compose.yml not found"
    exit 1
fi

log_info "Found docker-compose.yml: $COMPOSE_FILE"

# Check if already patched (idempotency)
if grep -q "traefik.enable=true" "$COMPOSE_FILE"; then
    log_success "Patch 005 already applied (Traefik labels found)"
    exit 0
fi

# Backup
BACKUP_DIR="/tmp/patch-002-backup"
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    log_info "Backing up docker-compose.yml to $BACKUP_DIR"
    cp "$COMPOSE_FILE" "$BACKUP_DIR/docker-compose.yml.backup"
else
    log_info "Backup already exists at $BACKUP_DIR"
fi

# ===================================================================
# Patch: Add Traefik Configuration to docker-compose.yml
# ===================================================================

log_info "Patching docker-compose.yml for Traefik..."

# Create temporary file for patched content
TMP_FILE=$(mktemp)

# Check if traefik-public network already exists in file
if grep -q "traefik-public:" "$COMPOSE_FILE"; then
    log_info "traefik-public network already defined"
else
    log_info "Adding traefik-public network definition..."

    # Add traefik-public network after blacklist-network
    awk '
    /^networks:/ { print; in_networks=1; next }
    in_networks && /^  blacklist-network:/ {
        print
        getline; print
        getline; print
        print "  traefik-public:"
        print "    external: true"
        print "    name: traefik-public"
        print ""
        in_networks=0
        next
    }
    { print }
    ' "$COMPOSE_FILE" > "$TMP_FILE"

    cp "$TMP_FILE" "$COMPOSE_FILE"
fi

# Add Traefik labels to blacklist-frontend service
if grep -q "blacklist-frontend:" "$COMPOSE_FILE"; then
    log_info "Adding Traefik labels to blacklist-frontend..."

    python3 << PYTHON_PATCH
import re
import sys

compose_file = "$COMPOSE_FILE"

with open(compose_file, 'r') as f:
    content = f.read()

# Find blacklist-frontend service section
frontend_pattern = r'(  blacklist-frontend:.*?)(  \S+:|^services:|^volumes:|^networks:|$)'
match = re.search(frontend_pattern, content, re.DOTALL | re.MULTILINE)

if not match:
    print("blacklist-frontend service not found")
    sys.exit(1)

frontend_section = match.group(1)
next_section = match.group(2)

# Check if networks already includes traefik-public
if 'traefik-public' not in frontend_section:
    # Add traefik-public to networks
    networks_pattern = r'(    networks:\n)(      - blacklist-network\n)'
    if re.search(networks_pattern, frontend_section):
        frontend_section = re.sub(
            networks_pattern,
            r'\1\2      - traefik-public\n',
            frontend_section
        )
    else:
        # No networks section, add it
        frontend_section = frontend_section.rstrip() + '\n    networks:\n      - blacklist-network\n      - traefik-public\n'

# Check if labels already exist
if 'labels:' not in frontend_section:
    # Add labels section before networks (or at end)
    labels = '''    labels:
      # Traefik - HTTPS Only (443)
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-public"
      - "traefik.http.routers.blacklist.rule=Host(`blacklist.nxtd.co.kr`)"
      - "traefik.http.routers.blacklist.entrypoints=websecure"
      - "traefik.http.routers.blacklist.tls=true"
      - "traefik.http.services.blacklist-frontend.loadbalancer.server.port=2543"
'''

    # Insert labels before networks section
    if 'networks:' in frontend_section:
        frontend_section = frontend_section.replace('    networks:', labels + '    networks:')
    else:
        frontend_section = frontend_section.rstrip() + '\n' + labels

# Replace in content
new_content = content.replace(match.group(0), frontend_section + next_section)

with open(compose_file, 'w') as f:
    f.write(new_content)

print("Traefik labels added successfully")
PYTHON_PATCH

    if [ $? -eq 0 ]; then
        log_success "Traefik labels added to blacklist-frontend"
    else
        log_error "Failed to add Traefik labels"
        # Restore from backup
        cp "$BACKUP_DIR/docker-compose.yml.backup" "$COMPOSE_FILE"
        exit 1
    fi
else
    log_warning "blacklist-frontend service not found in docker-compose.yml"
fi

# ===================================================================
# Verify Changes
# ===================================================================

log_info "Verifying changes..."

if grep -q "traefik.enable=true" "$COMPOSE_FILE"; then
    log_success "✓ Traefik labels present"
else
    log_error "✗ Traefik labels missing"
    exit 1
fi

if grep -q "traefik-public" "$COMPOSE_FILE"; then
    log_success "✓ traefik-public network configured"
else
    log_error "✗ traefik-public network missing"
    exit 1
fi

# ===================================================================
# Post-Patch Instructions
# ===================================================================

log_success "Patch 005 applied successfully!"
echo ""
log_info "Next Steps:"
log_info "==========="
log_info "1. Create traefik-public network (if not exists):"
log_info "   docker network create traefik-public"
echo ""
log_info "2. Ensure Traefik is running:"
log_info "   docker ps | grep traefik"
echo ""
log_info "3. Restart blacklist services:"
log_info "   docker compose restart blacklist-frontend"
echo ""
log_info "4. Verify Traefik routing:"
log_info "   docker logs traefik | grep blacklist"
echo ""
log_info "5. Test access:"
log_info "   curl -k https://blacklist.nxtd.co.kr"
echo ""
log_warning "Note: nginx container can be stopped if Traefik is active"
log_info "      docker compose stop blacklist-nginx"
echo ""
log_success "Traefik migration completed!"
