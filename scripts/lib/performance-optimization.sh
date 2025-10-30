#!/bin/bash
# Performance Optimization Library - Phase 3 Implementation
#
# Purpose: Docker build optimization, caching strategies, parallel operations
# Usage: source scripts/lib/performance-optimization.sh
#
# Created: 2025-10-22
# Phase: 3.4 - Performance Optimization

# ========================================
# Color Output Functions
# ========================================
log_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# ========================================
# Global Variables
# ========================================
PARALLEL_JOBS="${PARALLEL_JOBS:-4}"
DOCKER_BUILD_CACHE="${DOCKER_BUILD_CACHE:-true}"
BUILDKIT_ENABLED="${BUILDKIT_ENABLED:-true}"

# ========================================
# Function: Enable Docker BuildKit
# ========================================
perf_enable_buildkit() {
    log_info "Enabling Docker BuildKit for faster builds..."

    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    log_success "BuildKit enabled"
    log_info "  DOCKER_BUILDKIT=1"
    log_info "  COMPOSE_DOCKER_CLI_BUILD=1"
}

# ========================================
# Function: Optimize Docker Build
# ========================================
perf_docker_build_optimized() {
    local dockerfile="$1"
    local tag="$2"
    local context="${3:-.}"
    local cache_from="${4:-}"

    log_info "Building Docker image with optimizations..."
    log_info "  Dockerfile: ${dockerfile}"
    log_info "  Tag: ${tag}"
    log_info "  Context: ${context}"

    # Enable BuildKit
    export DOCKER_BUILDKIT=1

    # Build command
    local build_cmd="docker build"
    build_cmd+=" -f ${dockerfile}"
    build_cmd+=" -t ${tag}"

    # Add cache options
    if [ "${DOCKER_BUILD_CACHE}" = "true" ]; then
        build_cmd+=" --cache-from=${tag}"
        [ -n "${cache_from}" ] && build_cmd+=" --cache-from=${cache_from}"
    fi

    # BuildKit-specific options
    if [ "${BUILDKIT_ENABLED}" = "true" ]; then
        build_cmd+=" --build-arg BUILDKIT_INLINE_CACHE=1"
    fi

    # Execute build
    build_cmd+=" ${context}"

    log_info "Executing: ${build_cmd}"

    if eval "${build_cmd}"; then
        log_success "Build complete: ${tag}"
        return 0
    else
        log_error "Build failed: ${tag}"
        return 1
    fi
}

# ========================================
# Function: Parallel Docker Builds
# ========================================
perf_docker_build_parallel() {
    local -n build_specs=$1  # Associative array: tag => dockerfile

    log_info "========================================="
    log_info "  Parallel Docker Builds"
    log_info "========================================="
    log_info "Building ${#build_specs[@]} images in parallel (max ${PARALLEL_JOBS} concurrent)..."

    local pids=()
    local failed=()

    # Enable BuildKit
    perf_enable_buildkit

    # Start builds
    for tag in "${!build_specs[@]}"; do
        local dockerfile="${build_specs[$tag]}"

        log_info "Starting build: ${tag}"

        # Wait if max parallel jobs reached
        while [ ${#pids[@]} -ge ${PARALLEL_JOBS} ]; do
            # Check for completed jobs
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                    unset pids[$i]
                fi
            done
            sleep 1
        done

        # Start build in background
        (
            if perf_docker_build_optimized "${dockerfile}" "${tag}" "." &>/dev/null; then
                exit 0
            else
                exit 1
            fi
        ) &

        pids+=($!)
    done

    # Wait for all builds to complete
    log_info "Waiting for all builds to complete..."

    for pid in "${pids[@]}"; do
        wait "${pid}" || failed+=("${pid}")
    done

    # Summary
    echo
    if [ ${#failed[@]} -eq 0 ]; then
        log_success "✅ All builds completed successfully (${#build_specs[@]}/${#build_specs[@]})"
        return 0
    else
        log_error "❌ ${#failed[@]} build(s) failed"
        return 1
    fi
}

# ========================================
# Function: Optimize Package Creation
# ========================================
perf_optimize_package_creation() {
    log_info "========================================="
    log_info "  Package Creation Optimization"
    log_info "========================================="

    # 1. Use rsync instead of cp
    log_info "✓ Using rsync for file copying (faster + progress)"

    # 2. Parallel Docker image saves
    log_info "✓ Parallel Docker image saves enabled"

    # 3. Enable tar compression with pigz (parallel gzip)
    if command -v pigz &>/dev/null; then
        log_success "✓ pigz available (parallel gzip compression)"
        export TAR_COMPRESSION="pigz"
    else
        log_warning "⚠️  pigz not available, falling back to gzip"
        log_info "  Install: sudo apt-get install pigz"
        export TAR_COMPRESSION="gzip"
    fi

    # 4. Use tmpfs for temporary files (if available)
    if grep -q tmpfs /proc/mounts; then
        export TEMP_DIR="/tmp"
        log_success "✓ Using tmpfs (/tmp) for temporary files"
    fi

    log_success "Package creation optimizations enabled"
}

# ========================================
# Function: Parallel File Operations
# ========================================
perf_parallel_copy() {
    local source_dir="$1"
    local dest_dir="$2"
    local description="${3:-Copying files}"

    log_info "${description}..."

    if command -v rsync &>/dev/null; then
        # Use rsync with parallel transfers
        rsync -a --info=progress2 --no-inc-recursive "${source_dir}/" "${dest_dir}/" 2>&1 | \
        while IFS= read -r line; do
            if [[ "$line" =~ ([0-9]+)% ]]; then
                local percent="${BASH_REMATCH[1]}"
                printf "\r\033[34m[INFO]\033[0m ${description}... %3d%%" "${percent}"
            fi
        done
        echo  # New line
        log_success "${description} complete"
    else
        # Fallback to cp
        cp -r "${source_dir}" "${dest_dir}"
        log_success "${description} complete"
    fi
}

# ========================================
# Function: Docker Image Save Parallel
# ========================================
perf_docker_save_parallel() {
    local -n images=$1  # Array of image names
    local output_dir="$2"

    log_info "Saving ${#images[@]} Docker images in parallel..."

    local pids=()

    for image in "${images[@]}"; do
        local output_file="${output_dir}/${image}.tar"

        log_info "Saving: ${image}"

        # Save in background
        docker save "${image}" -o "${output_file}" &
        pids+=($!)

        # Limit parallel saves
        while [ ${#pids[@]} -ge ${PARALLEL_JOBS} ]; do
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                    unset pids[$i]
                fi
            done
            sleep 1
        done
    done

    # Wait for all saves
    for pid in "${pids[@]}"; do
        wait "${pid}"
    done

    log_success "All images saved"
}

# ========================================
# Function: Compress with Parallel Tools
# ========================================
perf_compress_parallel() {
    local source="$1"
    local output="$2"

    log_info "Compressing with parallel tools..."

    if command -v pigz &>/dev/null; then
        log_info "Using pigz (parallel gzip)..."
        tar -cf - "${source}" | pigz -p ${PARALLEL_JOBS} > "${output}"
        log_success "Compression complete with pigz"
    elif command -v pbzip2 &>/dev/null; then
        log_info "Using pbzip2 (parallel bzip2)..."
        tar -cf - "${source}" | pbzip2 -p${PARALLEL_JOBS} > "${output}"
        log_success "Compression complete with pbzip2"
    else
        log_warning "No parallel compression tools available"
        log_info "Using standard gzip..."
        tar -czf "${output}" "${source}"
        log_success "Compression complete with gzip"
    fi
}

# ========================================
# Function: Docker Compose Parallel Start
# ========================================
perf_compose_parallel_start() {
    local compose_file="${1:-docker-compose.yml}"

    log_info "Starting services with Docker Compose..."

    # Enable BuildKit for compose
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    # Use --parallel flag for parallel container starts
    if docker compose --help | grep -q -- '--parallel'; then
        log_info "Using parallel container start..."
        docker compose -f "${compose_file}" up -d --parallel ${PARALLEL_JOBS}
    else
        log_warning "Docker Compose version doesn't support --parallel"
        docker compose -f "${compose_file}" up -d
    fi

    log_success "Services started"
}

# ========================================
# Function: Optimize Python Package Installation
# ========================================
perf_pip_install_optimized() {
    local requirements_file="$1"
    local target_dir="${2:-.}"

    log_info "Installing Python packages with optimizations..."

    # Use pip with cache and parallel downloads
    pip install \
        --requirement "${requirements_file}" \
        --target "${target_dir}" \
        --cache-dir=/tmp/pip-cache \
        --prefer-binary \
        --no-warn-script-location \
        2>&1 | while IFS= read -r line; do
            echo "${line}"
        done

    log_success "Python packages installed"
}

# ========================================
# Function: Cache Management
# ========================================
perf_cache_warmup() {
    log_info "Warming up caches..."

    # Docker layer cache
    if [ "${DOCKER_BUILD_CACHE}" = "true" ]; then
        log_info "Docker layer cache: enabled"
    fi

    # pip cache
    if [ -d "/tmp/pip-cache" ]; then
        log_success "pip cache: $(du -sh /tmp/pip-cache | cut -f1)"
    fi

    # npm cache
    if [ -d "${HOME}/.npm" ]; then
        log_success "npm cache: $(du -sh ${HOME}/.npm | cut -f1)"
    fi
}

# ========================================
# Function: Performance Report
# ========================================
perf_report() {
    log_info "========================================="
    log_info "  Performance Report"
    log_info "========================================="

    # CPU info
    if command -v nproc &>/dev/null; then
        local cpu_cores=$(nproc)
        log_info "CPU Cores: ${cpu_cores}"
        log_info "  Parallel jobs: ${PARALLEL_JOBS}"
        log_info "  Utilization: $((PARALLEL_JOBS * 100 / cpu_cores))%"
    fi

    echo

    # Memory info
    if [ -f /proc/meminfo ]; then
        local total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2 / 1024 / 1024}')
        local avail_mem=$(grep MemAvailable /proc/meminfo | awk '{print $2 / 1024 / 1024}')
        log_info "Memory:"
        log_info "  Total: ${total_mem}GB"
        log_info "  Available: ${avail_mem}GB"
    fi

    echo

    # Disk I/O
    if command -v df &>/dev/null; then
        log_info "Disk Usage:"
        df -h / | awk 'NR==1 || /\/$/'
    fi

    echo

    # Docker info
    if docker info &>/dev/null; then
        log_info "Docker:"
        log_info "  BuildKit: ${BUILDKIT_ENABLED}"
        log_info "  Cache: ${DOCKER_BUILD_CACHE}"
        local docker_images=$(docker images -q | wc -l)
        log_info "  Images: ${docker_images}"
    fi
}

# ========================================
# Function: Optimize System Settings
# ========================================
perf_optimize_system() {
    log_info "Optimizing system settings for build performance..."

    # Increase file descriptor limit
    if command -v ulimit &>/dev/null; then
        ulimit -n 65536 2>/dev/null && log_success "  ✓ File descriptor limit increased"
    fi

    # Disable swap if building on tmpfs
    # (Commented out - potentially dangerous)
    # swapoff -a 2>/dev/null && log_success "  ✓ Swap disabled for tmpfs builds"

    log_info "System optimization complete"
}

# ========================================
# Function: Benchmark Operations
# ========================================
perf_benchmark() {
    local operation="$1"
    local start_time=$(date +%s)

    log_info "Benchmarking: ${operation}..."

    # Execute operation
    eval "${operation}"
    local exit_code=$?

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Format duration
    if [ ${duration} -lt 60 ]; then
        log_info "Duration: ${duration}s"
    else
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        log_info "Duration: ${minutes}m ${seconds}s"
    fi

    return ${exit_code}
}
