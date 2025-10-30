#!/bin/bash
#
# Patch 001: Upgrade Entrypoint with Smart Patch Detection
# ==========================================================
#
# Problem:
# 1. 기존 entrypoint.sh는 모든 패치를 매번 재실행
# 2. 불필요한 CPU/시간 소모, 복잡한 로그
#
# Solution:
# 1. 스마트 패치 감지 시스템으로 업그레이드
# 2. /app/.applied_patches 추적 파일로 적용된 패치 기록
# 3. 적용 안된 패치만 자동 스캔 및 실행
# 4. Applied/Skipped/Failed 통계 표시
#
# Version: 3.3.8+
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

log_info "Starting Patch 001: Upgrade Entrypoint with Smart Detection"
log_info "=============================================================="

# Check if running in container
if [ ! -f /.dockerenv ]; then
    log_error "This patch must be run inside Docker container"
    log_info "Usage: docker exec blacklist-app bash /patches/007-upgrade-entrypoint-smart-detection.sh"
    exit 1
fi

# Target file
ENTRYPOINT_FILE="/app/entrypoint.sh"

# Check if file exists
if [ ! -f "$ENTRYPOINT_FILE" ]; then
    log_error "entrypoint.sh not found at $ENTRYPOINT_FILE"
    exit 1
fi

# Check if already patched (idempotency)
if grep -q "is_patch_applied()" "$ENTRYPOINT_FILE"; then
    log_success "Patch 001 already applied (smart detection found)"
    exit 0
fi

# Backup
BACKUP_DIR="/tmp/patch-001-backup"
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    log_info "Backing up entrypoint.sh to $BACKUP_DIR"
    cp "$ENTRYPOINT_FILE" "$BACKUP_DIR/entrypoint.sh.backup"
else
    log_info "Backup already exists at $BACKUP_DIR"
fi

# ===================================================================
# Patch: Replace entrypoint.sh with smart detection version
# ===================================================================

log_info "Upgrading entrypoint.sh to smart detection version..."

cat > "$ENTRYPOINT_FILE" << 'ENTRYPOINT_EOF'
#!/bin/bash
#
# Blacklist Application Entrypoint
# =================================
# Auto-applies UNAPPLIED patches on container start (smart detection)
#
# Version: 3.3.8+
# Date: 2025-10-30
# Author: Claude Code

set -eo pipefail

# Color codes
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
NC=$'\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Blacklist Application Entrypoint${NC}"
echo -e "${BLUE}========================================${NC}"

# Applied patches tracking file
APPLIED_PATCHES_FILE="/app/.applied_patches"

# Create tracking file if not exists
if [ ! -f "$APPLIED_PATCHES_FILE" ]; then
    touch "$APPLIED_PATCHES_FILE"
    echo -e "${BLUE}📝 Created patch tracking file: $APPLIED_PATCHES_FILE${NC}"
fi

# Patch directories (support both absolute and relative paths)
PATCH_DIRS=(
    "/patches"                          # Volume mount (docker-compose.yml)
    "/app/patches"                      # Relative to app directory
    "./offline-packages/patches"        # Offline package path
)

# Find available patch directory
PATCH_DIR=""
for dir in "${PATCH_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$(ls -A "$dir"/*.sh 2>/dev/null)" ]; then
        PATCH_DIR="$dir"
        echo -e "${BLUE}📦 Patches directory found: $PATCH_DIR${NC}"
        break
    fi
done

# Function to check if patch already applied
is_patch_applied() {
    local patch_name="$1"
    grep -q "^${patch_name}$" "$APPLIED_PATCHES_FILE" 2>/dev/null
}

# Function to mark patch as applied
mark_patch_applied() {
    local patch_name="$1"
    echo "$patch_name" >> "$APPLIED_PATCHES_FILE"
}

# Apply patches if directory found
if [ -n "$PATCH_DIR" ]; then
    # Scan for available patches
    TOTAL_PATCHES=$(find "$PATCH_DIR" -name "*.sh" 2>/dev/null | wc -l)

    if [ "$TOTAL_PATCHES" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No patch files (.sh) found in $PATCH_DIR${NC}"
    else
        echo -e "${BLUE}🔍 Scanning patches: $TOTAL_PATCHES total${NC}"

        # Track applied patches
        APPLIED_COUNT=0
        SKIPPED_COUNT=0
        FAILED_COUNT=0

        # Apply only unapplied patches (sorted by name)
        for patch_file in $(ls "$PATCH_DIR"/*.sh 2>/dev/null | sort); do
            if [ -f "$patch_file" ]; then
                patch_name=$(basename "$patch_file")

                # Check if already applied
                if is_patch_applied "$patch_name"; then
                    echo -e "${BLUE}  ⊙ $patch_name (already applied, skipping)${NC}"
                    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
                    continue
                fi

                # Apply new patch
                echo -e "${YELLOW}  → Applying: $patch_name${NC}"

                # Execute patch (suppress output unless it fails)
                if bash "$patch_file" > /tmp/patch_${patch_name}.log 2>&1; then
                    echo -e "${GREEN}  ✓ $patch_name applied successfully${NC}"
                    mark_patch_applied "$patch_name"
                    APPLIED_COUNT=$((APPLIED_COUNT + 1))
                else
                    echo -e "${RED}  ✗ $patch_name failed (non-critical, continuing...)${NC}"
                    cat /tmp/patch_${patch_name}.log
                    FAILED_COUNT=$((FAILED_COUNT + 1))
                fi
            fi
        done

        # Summary
        echo -e "${GREEN}✓ Summary: Applied: $APPLIED_COUNT | Skipped: $SKIPPED_COUNT | Failed: $FAILED_COUNT${NC}"

        # Show applied patches history
        if [ -f "$APPLIED_PATCHES_FILE" ]; then
            HISTORY_COUNT=$(wc -l < "$APPLIED_PATCHES_FILE")
            echo -e "${BLUE}📋 Total patches in history: $HISTORY_COUNT${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  No patches directory found - skipping auto-patching${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Flask application...${NC}"
echo -e "${BLUE}========================================${NC}"

# Start Flask application
exec python run_app.py
ENTRYPOINT_EOF

# Set executable permissions
chmod +x "$ENTRYPOINT_FILE"

log_success "entrypoint.sh upgraded successfully"

# ===================================================================
# Verification
# ===================================================================

log_info ""
log_info "Verifying changes..."

# Check for smart detection functions
if grep -q "is_patch_applied()" "$ENTRYPOINT_FILE"; then
    log_success "✓ Smart detection functions present"
else
    log_error "✗ Smart detection functions missing"
    exit 1
fi

# Check for tracking file creation
if grep -q "APPLIED_PATCHES_FILE" "$ENTRYPOINT_FILE"; then
    log_success "✓ Patch tracking file configuration present"
else
    log_error "✗ Patch tracking file configuration missing"
    exit 1
fi

# Check executable permissions
if [ -x "$ENTRYPOINT_FILE" ]; then
    log_success "✓ Executable permissions set"
else
    log_error "✗ Executable permissions missing"
    exit 1
fi

# ===================================================================
# Post-Patch Instructions
# ===================================================================

log_success "Patch 001 applied successfully!"
echo ""
log_info "Next Steps:"
log_info "==========="
log_info "1. Restart container to use new entrypoint:"
log_info "   docker compose restart blacklist-app"
echo ""
log_info "2. Verify smart detection working:"
log_info "   docker logs blacklist-app | grep 'Scanning patches'"
echo ""
log_info "3. Check patch tracking file:"
log_info "   docker exec blacklist-app cat /app/.applied_patches"
echo ""
log_info "Expected behavior:"
log_info "  - First restart: All patches applied"
log_info "  - Second restart: All patches skipped (already applied)"
log_info "  - New patch added: Only new patch applied"
echo ""
log_warning "Note: This patch takes effect on NEXT container restart"
log_success "Entrypoint upgrade completed!"
