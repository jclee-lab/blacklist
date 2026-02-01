#!/bin/bash
# =============================================================================
# Blacklist Platform - Airgap Image Build Script
# =============================================================================
# 
# Description: Builds/exports all Docker images for airgap deployment
# Usage: ./build-airgap.sh [--from-lxc] [--frontend-only]
#
# Options:
#   --from-lxc      Export images from LXC 220 (default: build locally)
#   --frontend-only Build only frontend image
#   --no-compress   Skip compression (faster, larger files)
#
# Output: deploy/airgap/images/*.tar.gz + checksums.sha256
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
OUTPUT_DIR="${SCRIPT_DIR}/images"
BUNDLE_FILE="${PROJECT_ROOT}/blacklist-airgap.tar.gz"

# LXC Configuration
PVE_HOST="192.168.50.100"
LXC_ID="220"

# Image names
IMAGES=(
    "blacklist-frontend"
    "blacklist-app"
    "blacklist-collector"
    "blacklist-postgres"
    "blacklist-redis"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
FROM_LXC=false
FRONTEND_ONLY=false
COMPRESS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --from-lxc) FROM_LXC=true; shift ;;
        --frontend-only) FRONTEND_ONLY=true; shift ;;
        --no-compress) COMPRESS=false; shift ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# =============================================================================
# Functions
# =============================================================================

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if $FROM_LXC; then
        if ! ssh -o ConnectTimeout=5 root@${PVE_HOST} "pct exec ${LXC_ID} -- docker --version" &> /dev/null; then
            log_error "Cannot connect to LXC ${LXC_ID} on ${PVE_HOST}"
            exit 1
        fi
    fi
    
    log_info "Dependencies OK"
}

build_frontend() {
    log_info "Building frontend image..."
    
    cd "${PROJECT_ROOT}/frontend"
    
    docker build \
        --tag blacklist-frontend:latest \
        --file Dockerfile \
        .
    
    log_info "Frontend image built successfully"
    cd "${PROJECT_ROOT}"
}

export_image_local() {
    local image=$1
    local output="${OUTPUT_DIR}/${image}.tar.gz"
    
    if docker image inspect "${image}:latest" &> /dev/null; then
        log_info "Exporting ${image}..."
        if $COMPRESS; then
            docker save "${image}:latest" | gzip > "${output}"
        else
            docker save "${image}:latest" -o "${OUTPUT_DIR}/${image}.tar"
        fi
        log_info "Exported: $(ls -lh ${output} | awk '{print $5}')"
    else
        log_warn "Image ${image}:latest not found locally, skipping"
        return 1
    fi
}

export_image_from_lxc() {
    local image=$1
    local output="${OUTPUT_DIR}/${image}.tar.gz"
    
    log_info "Exporting ${image} from LXC ${LXC_ID}..."
    
    if $COMPRESS; then
        ssh root@${PVE_HOST} "pct exec ${LXC_ID} -- docker save ${image}:latest | gzip" > "${output}"
    else
        ssh root@${PVE_HOST} "pct exec ${LXC_ID} -- docker save ${image}:latest" > "${OUTPUT_DIR}/${image}.tar"
    fi
    
    log_info "Exported: $(ls -lh ${output} | awk '{print $5}')"
}

export_db_dump() {
    log_info "Exporting database dump from LXC ${LXC_ID}..."
    
    local output="${OUTPUT_DIR}/blacklist-db-dump.sql.gz"
    
    ssh root@${PVE_HOST} "pct exec ${LXC_ID} -- docker exec blacklist-postgres pg_dump -U blacklist -d blacklist | gzip" > "${output}"
    
    log_info "DB dump exported: $(ls -lh ${output} | awk '{print $5}')"
}

generate_checksums() {
    log_info "Generating checksums..."
    
    cd "${OUTPUT_DIR}"
    sha256sum *.tar.gz *.tar 2>/dev/null > checksums.sha256 || \
    sha256sum *.tar.gz > checksums.sha256
    
    log_info "Checksums generated"
    cat checksums.sha256
    cd "${PROJECT_ROOT}"
}

create_bundle() {
    log_info "Creating airgap bundle..."
    
    cd "${SCRIPT_DIR}"
    
    tar -czvf "${BUNDLE_FILE}" \
        docker-compose.yml \
        install.sh \
        images/
    
    cd "${PROJECT_ROOT}"
    
    # Add postgres migrations if they exist
    if [[ -d "${PROJECT_ROOT}/postgres/migrations" ]]; then
        log_info "Adding postgres migrations..."
        cd "${PROJECT_ROOT}"
        tar -rf "${BUNDLE_FILE%.gz}" postgres/migrations/
        gzip -f "${BUNDLE_FILE%.gz}"
    fi
    
    log_info "Bundle created: $(ls -lh ${BUNDLE_FILE} | awk '{print $5}')"
    sha256sum "${BUNDLE_FILE}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "=== Blacklist Airgap Build Script ==="
    log_info "Output directory: ${OUTPUT_DIR}"
    log_info "Mode: $(if $FROM_LXC; then echo 'Export from LXC'; else echo 'Build locally'; fi)"
    
    check_dependencies
    
    # Create output directory
    mkdir -p "${OUTPUT_DIR}"
    
    if $FRONTEND_ONLY; then
        # Build and export frontend only
        build_frontend
        export_image_local "blacklist-frontend"
    elif $FROM_LXC; then
        # Export all images from LXC 220
        for image in "${IMAGES[@]}"; do
            export_image_from_lxc "${image}"
        done
        export_db_dump
    else
        # Build frontend locally, export others if available
        build_frontend
        
        for image in "${IMAGES[@]}"; do
            export_image_local "${image}" || true
        done
    fi
    
    generate_checksums
    create_bundle
    
    log_info "=== Build Complete ==="
    log_info ""
    log_info "Files created:"
    ls -lh "${OUTPUT_DIR}/"
    log_info ""
    log_info "Bundle: ${BUNDLE_FILE}"
    log_info ""
    log_info "To install on airgap system:"
    log_info "  1. Copy ${BUNDLE_FILE} to target system"
    log_info "  2. tar -xzf blacklist-airgap.tar.gz"
    log_info "  3. ./install.sh"
}

main "$@"
