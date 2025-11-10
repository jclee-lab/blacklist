#!/bin/bash
# Build and Push Docker Images to Registry
# Usage: ./scripts/build-and-push.sh [component] [--no-cache]
#
# Components: postgres, redis, collector, app, frontend, all (default)
# Options: --no-cache (force rebuild without cache)

set -e

# Configuration
REGISTRY_HOST="${REGISTRY_HOST:-registry.jclee.me}"
VERSION_TAG="${VERSION_TAG:-latest}"
COMMIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Component definitions
declare -A COMPONENTS=(
    ["postgres"]="postgres/Dockerfile"
    ["redis"]="redis/Dockerfile"
    ["collector"]="collector/Dockerfile"
    ["app"]="app/Dockerfile"
    ["frontend"]="frontend/Dockerfile"
)

# Functions
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

show_usage() {
    cat <<EOF
Usage: $0 [component] [options]

Components:
  all         Build and push all components (default)
  postgres    PostgreSQL database with auto-migrations
  redis       Redis cache server
  collector   REGTECH/SECUDIUM data collector
  app         Flask backend application
  frontend    Next.js frontend application

Options:
  --no-cache  Force rebuild without using cache
  --help      Show this help message

Examples:
  $0                  # Build and push all components
  $0 app              # Build and push app only
  $0 all --no-cache   # Rebuild all from scratch

EOF
}

check_registry_login() {
    log_info "Checking registry login status..."

    # Check if credentials exist in docker config
    if grep -q "$REGISTRY_HOST" ~/.docker/config.json 2>/dev/null; then
        log_success "Registry login verified (credentials found)"
        return 0
    fi

    # Fallback: check docker info
    if docker info 2>/dev/null | grep -q "$REGISTRY_HOST"; then
        log_success "Registry login verified"
        return 0
    fi

    log_warning "Not logged into registry $REGISTRY_HOST"
    log_info "Please login first:"
    echo ""
    echo "  docker login $REGISTRY_HOST"
    echo ""
    exit 1
}

build_image() {
    local component=$1
    local dockerfile=$2
    local no_cache_flag=$3

    local context_dir=$(dirname "$dockerfile")
    local image_name="blacklist-${component}"
    local full_image="${REGISTRY_HOST}/${image_name}"

    log_info "Building ${component}..."
    log_info "  Context: ${context_dir}"
    log_info "  Dockerfile: ${dockerfile}"
    log_info "  Image: ${full_image}:${VERSION_TAG}"

    local build_args=(
        "--platform" "linux/amd64"
        "--build-arg" "BUILD_DATE=${BUILD_DATE}"
        "--build-arg" "VCS_REF=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
        "--build-arg" "BUILDKIT_INLINE_CACHE=1"
        "--tag" "${full_image}:${VERSION_TAG}"
        "--tag" "${full_image}:${COMMIT_SHORT}"
        "--file" "${dockerfile}"
    )

    if [ "$no_cache_flag" == "true" ]; then
        build_args+=("--no-cache")
        log_info "  Cache: disabled (--no-cache)"
    else
        build_args+=("--cache-from" "${full_image}:latest")
        log_info "  Cache: enabled (from ${full_image}:latest)"
    fi

    build_args+=("${context_dir}")

    if docker build "${build_args[@]}"; then
        log_success "Build completed: ${component}"
        return 0
    else
        log_error "Build failed: ${component}"
        return 1
    fi
}

push_image() {
    local component=$1
    local image_name="blacklist-${component}"
    local full_image="${REGISTRY_HOST}/${image_name}"

    log_info "Pushing ${component} to registry..."

    # Push latest tag
    log_info "  Pushing ${full_image}:${VERSION_TAG}..."
    if docker push "${full_image}:${VERSION_TAG}"; then
        log_success "Pushed: ${full_image}:${VERSION_TAG}"
    else
        log_error "Failed to push: ${full_image}:${VERSION_TAG}"
        return 1
    fi

    # Push commit tag
    log_info "  Pushing ${full_image}:${COMMIT_SHORT}..."
    if docker push "${full_image}:${COMMIT_SHORT}"; then
        log_success "Pushed: ${full_image}:${COMMIT_SHORT}"
    else
        log_error "Failed to push: ${full_image}:${COMMIT_SHORT}"
        return 1
    fi

    return 0
}

build_and_push() {
    local component=$1
    local dockerfile=$2
    local no_cache=$3

    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Processing component: ${component}"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Build
    if ! build_image "$component" "$dockerfile" "$no_cache"; then
        log_error "Skipping push due to build failure"
        return 1
    fi

    # Push
    if ! push_image "$component"; then
        log_error "Push failed for component: ${component}"
        return 1
    fi

    log_success "Completed: ${component}"
    return 0
}

# Main script
main() {
    local target_component="all"
    local no_cache="false"

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_usage
                exit 0
                ;;
            --no-cache)
                no_cache="true"
                shift
                ;;
            postgres|redis|collector|app|frontend|all)
                target_component="$1"
                shift
                ;;
            *)
                log_error "Unknown argument: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Display banner
    echo ""
    log_info "═══════════════════════════════════════════════"
    log_info "  Docker Build & Push to Registry"
    log_info "═══════════════════════════════════════════════"
    log_info "Registry: ${REGISTRY_HOST}"
    log_info "Version: ${VERSION_TAG}"
    log_info "Commit: ${COMMIT_SHORT}"
    log_info "Target: ${target_component}"
    log_info "No Cache: ${no_cache}"
    log_info "═══════════════════════════════════════════════"
    echo ""

    # Check registry login
    check_registry_login

    # Process components
    local failed_components=()

    if [ "$target_component" == "all" ]; then
        # Build all components
        for component in "${!COMPONENTS[*]}"; do
            if ! build_and_push "$component" "${COMPONENTS[$component]}" "$no_cache"; then
                failed_components+=("$component")
            fi
        done
    else
        # Build single component
        if [ -z "${COMPONENTS[$target_component]}" ]; then
            log_error "Unknown component: $target_component"
            log_info "Available components: ${!COMPONENTS[*]}"
            exit 1
        fi

        if ! build_and_push "$target_component" "${COMPONENTS[$target_component]}" "$no_cache"; then
            failed_components+=("$target_component")
        fi
    fi

    # Summary
    echo ""
    log_info "═══════════════════════════════════════════════"
    log_info "  Build & Push Summary"
    log_info "═══════════════════════════════════════════════"

    if [ ${#failed_components[@]} -eq 0 ]; then
        log_success "All components completed successfully!"
        log_info ""
        log_info "Next steps:"
        log_info "  1. Check registry: https://registry.jclee.me"
        log_info "  2. Deploy via Portainer webhook or docker-compose"
        log_info "  3. Verify health: curl https://blacklist.nxtd.co.kr/health"
    else
        log_error "Failed components: ${failed_components[*]}"
        exit 1
    fi

    log_info "═══════════════════════════════════════════════"
    echo ""
}

# Run main function
main "$@"
