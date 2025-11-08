#!/bin/bash
# ============================================================================
# Sequential Image Packaging Script
# ============================================================================
# Packages all images one by one (more reliable than parallel)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

# Services in order (smallest to largest)
SERVICES=(
    "blacklist-redis"
    "blacklist-frontend"
    "blacklist-postgres"
    "blacklist-app"
    "blacklist-collector"
)

echo "============================================"
echo "🐳 Sequential Image Packaging"
echo "============================================"
echo ""
log_info "Will package ${#SERVICES[@]} images sequentially"
echo ""

SUCCESS=0
FAILED=0

for service in "${SERVICES[@]}"; do
    log_info "Packaging: $service"
    echo ""

    if "$SCRIPT_DIR/package-single-image.sh" "$service"; then
        ((SUCCESS++))
        echo ""
        log_success "✓ $service packaged successfully"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    else
        ((FAILED++))
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
done

echo ""
echo "============================================"
echo "📊 Packaging Summary"
echo "============================================"
echo "  ✅ Success: $SUCCESS/${#SERVICES[@]}"
if [ $FAILED -gt 0 ]; then
    echo "  ❌ Failed:  $FAILED/${#SERVICES[@]}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    log_success "All images packaged successfully!"
    echo ""
    log_info "Output directory:"
    ls -lh "$(dirname "$SCRIPT_DIR")/dist/images/"
else
    exit 1
fi
