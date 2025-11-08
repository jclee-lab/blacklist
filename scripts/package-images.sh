#!/bin/bash
# ============================================================================
# Docker Image Packaging Script
# ============================================================================
# Purpose: Package all Docker images for offline deployment
# Usage: ./scripts/package-images.sh [output_dir]
# Output: Compressed tar files for each service
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-${PROJECT_ROOT}/dist/images}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Service configurations
declare -A SERVICES=(
    ["blacklist-postgres"]="blacklist-postgres:offline"
    ["blacklist-app"]="blacklist-app:offline"
    ["blacklist-collector"]="blacklist-collector:offline"
    ["blacklist-frontend"]="blacklist-frontend:offline"
    ["blacklist-redis"]="blacklist-redis:offline"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

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

# ============================================================================
# Validation Functions
# ============================================================================
check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    if ! command -v gzip &> /dev/null; then
        missing_deps+=("gzip")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi

    log_success "All dependencies available"
}

verify_images_exist() {
    log_info "Verifying Docker images..."

    local missing_images=()

    for service in "${!SERVICES[@]}"; do
        local image="${SERVICES[$service]}"
        if ! docker image inspect "$image" &> /dev/null; then
            missing_images+=("$image")
        fi
    done

    if [ ${#missing_images[@]} -ne 0 ]; then
        log_error "Missing images: ${missing_images[*]}"
        log_info "Run 'docker-compose build' first"
        exit 1
    fi

    log_success "All images exist"
}

# ============================================================================
# Image Information
# ============================================================================
display_image_info() {
    log_info "Docker Image Information:"
    echo ""
    printf "%-25s %-30s %-15s %-20s\n" "SERVICE" "IMAGE" "SIZE" "CREATED"
    printf "%-25s %-30s %-15s %-20s\n" "-------" "-----" "----" "-------"

    for service in "${!SERVICES[@]}"; do
        local image="${SERVICES[$service]}"
        local size
        local created
        local human_size
        size=$(docker image inspect "$image" --format='{{.Size}}')
        created=$(docker image inspect "$image" --format='{{.Created}}' | cut -d'T' -f1)
        human_size=$(human_readable_size "$size")

        printf "%-25s %-30s %-15s %-20s\n" "$service" "$image" "$human_size" "$created"
    done
    echo ""
}

# ============================================================================
# Packaging Functions
# ============================================================================
create_output_directory() {
    log_info "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
    log_success "Output directory ready"
}

package_image() {
    local service=$1
    local image=$2
    local output_file="${OUTPUT_DIR}/${service}_${TIMESTAMP}.tar.gz"

    log_info "Packaging $service ($image)..."

    # Save Docker image to tar
    local temp_tar="/tmp/${service}_${TIMESTAMP}.tar"
    if docker save -o "$temp_tar" "$image"; then
        log_success "Image saved to temporary file"
    else
        log_error "Failed to save image"
        return 1
    fi

    # Compress tar file
    log_info "Compressing ${service}..."
    if gzip -c "$temp_tar" > "$output_file"; then
        local original_size
        local compressed_size
        local ratio
        original_size=$(stat -f%z "$temp_tar" 2>/dev/null || stat -c%s "$temp_tar")
        compressed_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file")
        ratio=$(awk "BEGIN {printf \"%.1f\", (1 - $compressed_size/$original_size) * 100}")

        log_success "Compressed: $(human_readable_size "$original_size") → $(human_readable_size "$compressed_size") (${ratio}% reduction)"

        # Cleanup temporary file
        rm -f "$temp_tar"

        return 0
    else
        log_error "Compression failed"
        rm -f "$temp_tar"
        return 1
    fi
}

package_all_images() {
    log_info "Starting image packaging..."
    echo ""

    local success_count=0
    local fail_count=0
    local total_count=${#SERVICES[@]}
    local current=0

    # Sort services for consistent ordering
    local sorted_services
    IFS=$'\n' read -r -d '' -a sorted_services < <(for key in "${!SERVICES[@]}"; do echo "$key"; done | sort && printf '\0')

    for service in "${sorted_services[@]}"; do
        ((current++))
        local image="${SERVICES[$service]}"

        log_info "Progress: $current/$total_count"

        if package_image "$service" "$image"; then
            ((success_count++))
        else
            ((fail_count++))
            log_warning "Continuing with next image..."
        fi
        echo ""
    done

    log_info "Packaging Summary:"
    echo "  ✅ Success: $success_count/$total_count"
    if [ $fail_count -gt 0 ]; then
        echo "  ❌ Failed: $fail_count/$total_count"
    fi
    echo ""
}

# ============================================================================
# Manifest Generation
# ============================================================================
generate_manifest() {
    local manifest_file="${OUTPUT_DIR}/manifest_${TIMESTAMP}.json"

    log_info "Generating manifest..."

    cat > "$manifest_file" << EOF
{
  "packaging_date": "$(date -Iseconds)",
  "packaging_host": "$(hostname)",
  "packaging_user": "$(whoami)",
  "images": [
EOF

    local first=true
    for service in "${!SERVICES[@]}"; do
        local image="${SERVICES[$service]}"
        local size
        local created
        local id
        size=$(docker image inspect "$image" --format='{{.Size}}')
        created=$(docker image inspect "$image" --format='{{.Created}}')
        id=$(docker image inspect "$image" --format='{{.Id}}')
        local archive_file="${service}_${TIMESTAMP}.tar.gz"

        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$manifest_file"
        fi

        cat >> "$manifest_file" << EOF
    {
      "service": "$service",
      "image": "$image",
      "image_id": "$id",
      "image_size": $size,
      "created": "$created",
      "archive_file": "$archive_file"
    }
EOF
    done

    cat >> "$manifest_file" << EOF

  ]
}
EOF

    log_success "Manifest created: $manifest_file"
}

# ============================================================================
# Deployment Script Generation
# ============================================================================
generate_deployment_script() {
    local deploy_script="${OUTPUT_DIR}/deploy_${TIMESTAMP}.sh"

    log_info "Generating deployment script..."

    cat > "$deploy_script" << 'DEPLOY_SCRIPT_EOF'
#!/bin/bash
# ============================================================================
# Docker Image Deployment Script
# ============================================================================
# Purpose: Load and deploy packaged Docker images
# Usage: ./deploy.sh
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

log_info "Starting Docker image deployment..."
echo ""

# Find all tar.gz files
for archive in "$SCRIPT_DIR"/*.tar.gz; do
    if [ -f "$archive" ]; then
        log_info "Loading $(basename "$archive")..."

        if gunzip -c "$archive" | docker load; then
            log_success "Loaded successfully"
        else
            log_error "Failed to load $archive"
            exit 1
        fi
        echo ""
    fi
done

log_success "All images loaded!"
echo ""
log_info "Verify with: docker images"
DEPLOY_SCRIPT_EOF

    chmod +x "$deploy_script"
    log_success "Deployment script created: $deploy_script"
}

# ============================================================================
# Summary Report
# ============================================================================
generate_summary() {
    log_info "Packaging Summary Report"
    echo ""
    echo "📦 Output Directory: $OUTPUT_DIR"
    echo "📅 Timestamp: $TIMESTAMP"
    echo ""

    log_info "Packaged Files:"
    find "$OUTPUT_DIR" -name "*_${TIMESTAMP}.tar.gz" -type f -exec ls -lh {} \; | awk '{printf "  %s  %s\n", $5, $9}'
    echo ""

    local total_size
    total_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
    echo "💾 Total Size: $total_size"
    echo ""

    log_info "Next Steps:"
    echo "  1. Copy entire directory to target server:"
    echo "     scp -r $OUTPUT_DIR user@server:/path/to/destination"
    echo ""
    echo "  2. On target server, run deployment script:"
    echo "     cd /path/to/destination/$(basename "$OUTPUT_DIR")"
    echo "     ./deploy_${TIMESTAMP}.sh"
    echo ""
    echo "  3. Start services:"
    echo "     docker-compose up -d"
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "============================================"
    echo "🐳 Docker Image Packaging Tool"
    echo "============================================"
    echo ""

    # Validation
    check_dependencies
    verify_images_exist

    # Display image information
    display_image_info

    # Create output directory
    create_output_directory

    # Package all images
    package_all_images

    # Generate manifest
    generate_manifest

    # Generate deployment script
    generate_deployment_script

    # Summary
    generate_summary

    log_success "Packaging completed successfully!"
}

# ============================================================================
# Script Entry Point
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
