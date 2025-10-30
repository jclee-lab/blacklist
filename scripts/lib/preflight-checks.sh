#!/bin/bash
# Pre-flight Checks Library - Phase 3 Implementation
#
# Purpose: Validate environment before installation/deployment
# Usage: source scripts/lib/preflight-checks.sh
#
# Created: 2025-10-22
# Phase: 3.1 - Pre-flight Checks

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
PREFLIGHT_ERRORS=0
PREFLIGHT_WARNINGS=0
PREFLIGHT_CHECKS_PASSED=0
PREFLIGHT_CHECKS_FAILED=0

# Required disk space (GB)
REQUIRED_DISK_SPACE_GB=${REQUIRED_DISK_SPACE_GB:-30}

# Required ports
REQUIRED_PORTS=(2542 2543 5432 6379 443 80)

# Docker minimum version
DOCKER_MIN_VERSION="20.10"
DOCKER_COMPOSE_MIN_VERSION="2.0"

# ========================================
# Function: Run All Pre-flight Checks
# ========================================
preflight_run_all() {
    log_info "========================================="
    log_info "  Pre-flight Checks (Phase 3)"
    log_info "========================================="
    echo

    # Reset counters
    PREFLIGHT_ERRORS=0
    PREFLIGHT_WARNINGS=0
    PREFLIGHT_CHECKS_PASSED=0
    PREFLIGHT_CHECKS_FAILED=0

    # Run all checks
    preflight_check_docker
    preflight_check_docker_compose
    preflight_check_disk_space
    preflight_check_ports
    preflight_check_network
    preflight_check_permissions
    preflight_check_system_resources

    # Summary
    echo
    log_info "========================================="
    log_info "  Pre-flight Check Summary"
    log_info "========================================="
    log_success "Passed: ${PREFLIGHT_CHECKS_PASSED}"

    if [ "${PREFLIGHT_CHECKS_FAILED}" -gt 0 ]; then
        log_error "Failed: ${PREFLIGHT_CHECKS_FAILED}"
    fi

    if [ "${PREFLIGHT_WARNINGS}" -gt 0 ]; then
        log_warning "Warnings: ${PREFLIGHT_WARNINGS}"
    fi

    if [ "${PREFLIGHT_ERRORS}" -gt 0 ]; then
        log_error "Errors: ${PREFLIGHT_ERRORS}"
    fi

    echo
    if [ "${PREFLIGHT_ERRORS}" -eq 0 ]; then
        log_success "✅ All critical pre-flight checks passed"
        return 0
    else
        log_error "❌ Pre-flight checks failed with ${PREFLIGHT_ERRORS} error(s)"
        return 1
    fi
}

# ========================================
# Check 1: Docker Daemon
# ========================================
preflight_check_docker() {
    log_info "[Check 1/7] Docker daemon status"

    if ! command -v docker &>/dev/null; then
        log_error "  ✗ Docker is not installed"
        log_error "    Install: https://docs.docker.com/engine/install/"
        PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
        PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
        return 1
    fi

    if ! docker info &>/dev/null; then
        log_error "  ✗ Docker daemon is not running"
        log_error "    Start: sudo systemctl start docker"
        log_error "    Enable: sudo systemctl enable docker"
        PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
        PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
        return 1
    fi

    # Check Docker version
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
    log_success "  ✓ Docker daemon is running (v${DOCKER_VERSION})"

    # Version comparison (simple)
    if [[ "${DOCKER_VERSION}" < "${DOCKER_MIN_VERSION}" ]]; then
        log_warning "  ⚠️  Docker version ${DOCKER_VERSION} is older than recommended ${DOCKER_MIN_VERSION}"
        PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
    fi

    PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    return 0
}

# ========================================
# Check 2: Docker Compose
# ========================================
preflight_check_docker_compose() {
    log_info "[Check 2/7] Docker Compose availability"

    # Check for docker compose (plugin) first
    if docker compose version &>/dev/null; then
        COMPOSE_VERSION=$(docker compose version --short 2>/dev/null)
        log_success "  ✓ Docker Compose plugin available (v${COMPOSE_VERSION})"
        PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
        return 0
    fi

    # Fallback to docker-compose (standalone)
    if command -v docker-compose &>/dev/null; then
        COMPOSE_VERSION=$(docker-compose version --short 2>/dev/null)
        log_success "  ✓ Docker Compose standalone available (v${COMPOSE_VERSION})"

        if [[ "${COMPOSE_VERSION}" < "${DOCKER_COMPOSE_MIN_VERSION}" ]]; then
            log_warning "  ⚠️  Docker Compose version ${COMPOSE_VERSION} is older than recommended ${DOCKER_COMPOSE_MIN_VERSION}"
            PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
        fi

        PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
        return 0
    fi

    log_error "  ✗ Docker Compose is not installed"
    log_error "    Install: https://docs.docker.com/compose/install/"
    PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
    PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
    return 1
}

# ========================================
# Check 3: Disk Space
# ========================================
preflight_check_disk_space() {
    log_info "[Check 3/7] Disk space availability"

    # Get available space in GB
    if command -v df &>/dev/null; then
        AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')

        if [ -z "${AVAILABLE_GB}" ]; then
            log_warning "  ⚠️  Could not determine available disk space"
            PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
            return 0
        fi

        if [ "${AVAILABLE_GB}" -lt "${REQUIRED_DISK_SPACE_GB}" ]; then
            log_error "  ✗ Insufficient disk space"
            log_error "    Available: ${AVAILABLE_GB}GB"
            log_error "    Required: ${REQUIRED_DISK_SPACE_GB}GB"
            log_error "    Free up space or use different installation directory"
            PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
            PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
            return 1
        fi

        log_success "  ✓ Disk space: ${AVAILABLE_GB}GB available (${REQUIRED_DISK_SPACE_GB}GB required)"
        PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    else
        log_warning "  ⚠️  'df' command not available, skipping disk space check"
        PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
    fi

    return 0
}

# ========================================
# Check 4: Port Conflicts
# ========================================
preflight_check_ports() {
    log_info "[Check 4/7] Port availability"

    CONFLICTS=0
    CONFLICTING_PORTS=()

    for PORT in "${REQUIRED_PORTS[@]}"; do
        # Check if port is in use (using netstat or ss)
        if command -v netstat &>/dev/null; then
            if netstat -tuln 2>/dev/null | grep -q ":${PORT} "; then
                CONFLICTING_PORTS+=("${PORT}")
                CONFLICTS=$((CONFLICTS + 1))
            fi
        elif command -v ss &>/dev/null; then
            if ss -tuln 2>/dev/null | grep -q ":${PORT} "; then
                CONFLICTING_PORTS+=("${PORT}")
                CONFLICTS=$((CONFLICTS + 1))
            fi
        fi
    done

    if [ "${CONFLICTS}" -eq 0 ]; then
        log_success "  ✓ All required ports available: ${REQUIRED_PORTS[*]}"
        PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    else
        log_warning "  ⚠️  ${CONFLICTS} port(s) in use: ${CONFLICTING_PORTS[*]}"
        log_warning "    This may cause deployment conflicts"
        log_warning "    Check with: netstat -tuln | grep -E ':(${CONFLICTING_PORTS[*]// /|})'"
        PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
    fi

    return 0
}

# ========================================
# Check 5: Network Connectivity
# ========================================
preflight_check_network() {
    log_info "[Check 5/7] Network connectivity"

    # Check if Docker network already exists
    if docker network ls 2>/dev/null | grep -q "blacklist-network"; then
        log_success "  ✓ Docker network 'blacklist-network' exists"
    else
        log_info "  ℹ️  Docker network 'blacklist-network' will be created during installation"
    fi

    # Check internet connectivity (for non-offline installations)
    if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
        log_success "  ✓ Internet connectivity available"
    else
        log_warning "  ⚠️  No internet connectivity (OK for offline installation)"
    fi

    PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    return 0
}

# ========================================
# Check 6: Permissions
# ========================================
preflight_check_permissions() {
    log_info "[Check 6/7] User permissions"

    # Check if user can run Docker commands
    if docker ps &>/dev/null; then
        log_success "  ✓ User can run Docker commands"
    else
        log_error "  ✗ User cannot run Docker commands"
        log_error "    Add user to docker group: sudo usermod -aG docker \$USER"
        log_error "    Then logout and login again"
        PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
        PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
        return 1
    fi

    # Check write permissions in current directory
    if [ -w "." ]; then
        log_success "  ✓ Write permissions in current directory"
    else
        log_error "  ✗ No write permissions in current directory"
        PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
        PREFLIGHT_CHECKS_FAILED=$((PREFLIGHT_CHECKS_FAILED + 1))
        return 1
    fi

    PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    return 0
}

# ========================================
# Check 7: System Resources
# ========================================
preflight_check_system_resources() {
    log_info "[Check 7/7] System resources"

    # Check available memory
    if [ -f "/proc/meminfo" ]; then
        TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))

        if [ "${TOTAL_MEM_GB}" -lt 4 ]; then
            log_warning "  ⚠️  Low memory: ${TOTAL_MEM_GB}GB (recommended: 4GB+)"
            PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
        else
            log_success "  ✓ Memory: ${TOTAL_MEM_GB}GB available"
        fi
    fi

    # Check CPU cores
    if command -v nproc &>/dev/null; then
        CPU_CORES=$(nproc)
        if [ "${CPU_CORES}" -lt 2 ]; then
            log_warning "  ⚠️  Low CPU cores: ${CPU_CORES} (recommended: 2+)"
            PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
        else
            log_success "  ✓ CPU cores: ${CPU_CORES}"
        fi
    fi

    PREFLIGHT_CHECKS_PASSED=$((PREFLIGHT_CHECKS_PASSED + 1))
    return 0
}

# ========================================
# Function: Interactive Pre-flight with Prompt
# ========================================
preflight_interactive() {
    preflight_run_all

    if [ "${PREFLIGHT_ERRORS}" -gt 0 ]; then
        echo
        log_error "Pre-flight checks failed with ${PREFLIGHT_ERRORS} error(s)"
        log_error "Please fix the errors above before continuing"
        return 1
    fi

    if [ "${PREFLIGHT_WARNINGS}" -gt 0 ]; then
        echo
        log_warning "Pre-flight checks completed with ${PREFLIGHT_WARNINGS} warning(s)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled by user"
            return 1
        fi
    fi

    return 0
}
