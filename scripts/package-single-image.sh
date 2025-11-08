#!/bin/bash
# ============================================================================
# Single Docker Image Packaging Script
# ============================================================================
# Usage: ./scripts/package-single-image.sh <service-name>
# Example: ./scripts/package-single-image.sh blacklist-frontend
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_ROOT}/dist/images"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Service to image mapping
declare -A IMAGES=(
    ["blacklist-postgres"]="blacklist-postgres:offline"
    ["blacklist-app"]="blacklist-app:offline"
    ["blacklist-collector"]="blacklist-collector:offline"
    ["blacklist-frontend"]="blacklist-frontend:offline"
    ["blacklist-redis"]="blacklist-redis:offline"
)

# Human readable size
human_readable_size() {
    local bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1024}")KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1073741824}")GB"
    fi
}

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <service-name>"
    echo ""
    echo "Available services:"
    for service in "${!IMAGES[@]}"; do
        echo "  - $service"
    done
    exit 1
fi

SERVICE=$1
IMAGE="${IMAGES[$SERVICE]}"

if [ -z "$IMAGE" ]; then
    log_error "Unknown service: $SERVICE"
    echo ""
    echo "Available services:"
    for service in "${!IMAGES[@]}"; do
        echo "  - $service"
    done
    exit 1
fi

echo "============================================"
echo "🐳 Single Image Packaging"
echo "============================================"
echo ""

# Check docker
if ! command -v docker &> /dev/null; then
    log_error "Docker not found"
    exit 1
fi

# Check gzip
if ! command -v gzip &> /dev/null; then
    log_error "gzip not found"
    exit 1
fi

log_success "Dependencies OK"

# Check image exists
if ! docker image inspect "$IMAGE" &> /dev/null; then
    log_error "Image not found: $IMAGE"
    exit 1
fi

log_success "Image exists: $IMAGE"

# Get image info
SIZE=$(docker image inspect "$IMAGE" --format='{{.Size}}')
CREATED=$(docker image inspect "$IMAGE" --format='{{.Created}}' | cut -dT -f1)
HUMAN_SIZE=$(human_readable_size "$SIZE")

echo ""
log_info "Image: $IMAGE"
log_info "Size: $HUMAN_SIZE"
log_info "Created: $CREATED"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
log_success "Output directory: $OUTPUT_DIR"
echo ""

# Package
OUTPUT_FILE="${OUTPUT_DIR}/${SERVICE}_${TIMESTAMP}.tar.gz"
TEMP_TAR="/tmp/${SERVICE}_${TIMESTAMP}.tar"

log_info "Step 1/3: Saving Docker image to tar..."
if docker save -o "$TEMP_TAR" "$IMAGE"; then
    log_success "Image saved to temporary file"
else
    log_error "Failed to save image"
    exit 1
fi

echo ""
log_info "Step 2/3: Compressing with gzip..."
if gzip -c "$TEMP_TAR" > "$OUTPUT_FILE"; then
    ORIGINAL_SIZE=$(stat -c%s "$TEMP_TAR" 2>/dev/null)
    COMPRESSED_SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    RATIO=$(awk "BEGIN {printf \"%.1f\", (1 - $COMPRESSED_SIZE/$ORIGINAL_SIZE) * 100}")

    log_success "Compressed successfully"
    echo "  Original:   $(human_readable_size "$ORIGINAL_SIZE")"
    echo "  Compressed: $(human_readable_size "$COMPRESSED_SIZE")"
    echo "  Reduction:  ${RATIO}%"
else
    log_error "Compression failed"
    rm -f "$TEMP_TAR"
    exit 1
fi

echo ""
log_info "Step 3/3: Cleaning up..."
rm -f "$TEMP_TAR"
log_success "Temporary files removed"

echo ""
echo "============================================"
log_success "Packaging completed!"
echo "============================================"
echo ""
echo "📦 Output: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Copy to target server:"
echo "     scp $OUTPUT_FILE user@server:/path/to/"
echo ""
echo "  2. Load on target server:"
echo "     gunzip -c $(basename "$OUTPUT_FILE") | docker load"
echo ""
