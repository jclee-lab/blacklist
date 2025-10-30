#!/bin/bash
# Health Monitoring Library - Phase 3 Implementation
#
# Purpose: Monitor service health and system status
# Usage: source scripts/lib/health-monitoring.sh
#
# Created: 2025-10-22
# Phase: 3.2 - Health Checks & Monitoring

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
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-30}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-5}
HEALTH_CHECK_MAX_RETRIES=${HEALTH_CHECK_MAX_RETRIES:-6}

# Service names
SERVICES=("blacklist-app" "blacklist-collector" "blacklist-postgres" "blacklist-redis" "blacklist-frontend" "blacklist-nginx")

# ========================================
# Function: Check Single Service Health
# ========================================
health_check_service() {
    local service_name="$1"
    local timeout="${2:-${HEALTH_CHECK_TIMEOUT}}"

    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${service_name}$"; then
        log_warning "  ⚠️  Container '${service_name}' does not exist"
        return 2
    fi

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${service_name}$"; then
        log_error "  ✗ Container '${service_name}' is not running"
        return 1
    fi

    # Check Docker health status
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "${service_name}" 2>/dev/null)

    if [ -z "${health_status}" ] || [ "${health_status}" = "<no value>" ]; then
        # No healthcheck defined, consider running as healthy
        log_success "  ✓ ${service_name}: running (no healthcheck)"
        return 0
    fi

    case "${health_status}" in
        "healthy")
            log_success "  ✓ ${service_name}: healthy"
            return 0
            ;;
        "unhealthy")
            log_error "  ✗ ${service_name}: unhealthy"
            return 1
            ;;
        "starting")
            log_info "  ⟳ ${service_name}: starting..."
            return 3
            ;;
        *)
            log_warning "  ⚠️  ${service_name}: unknown status (${health_status})"
            return 2
            ;;
    esac
}

# ========================================
# Function: Wait for Service to be Healthy
# ========================================
health_wait_for_service() {
    local service_name="$1"
    local max_retries="${2:-${HEALTH_CHECK_MAX_RETRIES}}"
    local interval="${3:-${HEALTH_CHECK_INTERVAL}}"

    log_info "Waiting for ${service_name} to be healthy..."

    local retry=0
    while [ ${retry} -lt ${max_retries} ]; do
        health_check_service "${service_name}" &>/dev/null
        local status=$?

        case ${status} in
            0)  # Healthy
                log_success "✓ ${service_name} is healthy (after $((retry * interval))s)"
                return 0
                ;;
            3)  # Starting
                printf "\r\033[34m[INFO]\033[0m ${service_name} starting... (%d/%d)" $((retry + 1)) "${max_retries}"
                ;;
            *)  # Unhealthy or error
                printf "\r\033[33m[WARNING]\033[0m ${service_name} not ready... (%d/%d)" $((retry + 1)) "${max_retries}"
                ;;
        esac

        sleep "${interval}"
        retry=$((retry + 1))
    done

    echo  # New line after progress
    log_error "✗ ${service_name} failed to become healthy after $((max_retries * interval))s"
    return 1
}

# ========================================
# Function: Check All Services
# ========================================
health_check_all_services() {
    log_info "========================================="
    log_info "  Service Health Check"
    log_info "========================================="

    local healthy=0
    local unhealthy=0
    local starting=0
    local missing=0

    for service in "${SERVICES[@]}"; do
        health_check_service "${service}"
        local status=$?

        case ${status} in
            0) healthy=$((healthy + 1)) ;;
            1) unhealthy=$((unhealthy + 1)) ;;
            2) missing=$((missing + 1)) ;;
            3) starting=$((starting + 1)) ;;
        esac
    done

    echo
    log_info "Summary:"
    log_success "  Healthy: ${healthy}/${#SERVICES[@]}"

    if [ ${unhealthy} -gt 0 ]; then
        log_error "  Unhealthy: ${unhealthy}"
    fi

    if [ ${starting} -gt 0 ]; then
        log_info "  Starting: ${starting}"
    fi

    if [ ${missing} -gt 0 ]; then
        log_warning "  Missing: ${missing}"
    fi

    if [ ${unhealthy} -eq 0 ] && [ ${healthy} -eq ${#SERVICES[@]} ]; then
        return 0
    else
        return 1
    fi
}

# ========================================
# Function: Wait for All Services
# ========================================
health_wait_for_all_services() {
    log_info "Waiting for all services to be healthy..."

    local failed_services=()

    for service in "${SERVICES[@]}"; do
        if ! health_wait_for_service "${service}"; then
            failed_services+=("${service}")
        fi
    done

    echo
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "✅ All services are healthy"
        return 0
    else
        log_error "❌ ${#failed_services[@]} service(s) failed to start: ${failed_services[*]}"
        return 1
    fi
}

# ========================================
# Function: HTTP Health Check
# ========================================
health_check_http() {
    local url="$1"
    local expected_status="${2:-200}"
    local timeout="${3:-5}"

    if command -v curl &>/dev/null; then
        local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "${timeout}" "${url}" 2>/dev/null)

        if [ "${status}" = "${expected_status}" ]; then
            log_success "  ✓ ${url}: HTTP ${status}"
            return 0
        else
            log_error "  ✗ ${url}: HTTP ${status} (expected ${expected_status})"
            return 1
        fi
    else
        log_warning "  ⚠️  curl not available, skipping HTTP health check"
        return 2
    fi
}

# ========================================
# Function: Database Health Check
# ========================================
health_check_database() {
    local db_host="${1:-blacklist-postgres}"
    local db_port="${2:-5432}"
    local db_name="${3:-blacklist}"
    local db_user="${4:-postgres}"

    log_info "Checking database connectivity..."

    # Try to connect via Docker exec
    if docker exec blacklist-postgres pg_isready -h localhost -p 5432 -U postgres &>/dev/null; then
        log_success "  ✓ PostgreSQL is ready"

        # Check if database exists
        if docker exec blacklist-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "${db_name}"; then
            log_success "  ✓ Database '${db_name}' exists"
            return 0
        else
            log_warning "  ⚠️  Database '${db_name}' does not exist"
            return 2
        fi
    else
        log_error "  ✗ PostgreSQL is not ready"
        return 1
    fi
}

# ========================================
# Function: Redis Health Check
# ========================================
health_check_redis() {
    local redis_host="${1:-blacklist-redis}"

    log_info "Checking Redis connectivity..."

    if docker exec blacklist-redis redis-cli ping &>/dev/null; then
        log_success "  ✓ Redis is responding (PONG)"
        return 0
    else
        log_error "  ✗ Redis is not responding"
        return 1
    fi
}

# ========================================
# Function: API Endpoints Health Check
# ========================================
health_check_api_endpoints() {
    log_info "Checking API endpoints..."

    local endpoints=(
        "http://localhost:2542/health"
        "http://localhost:2542/metrics"
    )

    local failed=0

    for endpoint in "${endpoints[@]}"; do
        if health_check_http "${endpoint}" 200 10; then
            :  # Success logged by health_check_http
        else
            failed=$((failed + 1))
        fi
    done

    if [ ${failed} -eq 0 ]; then
        log_success "✓ All API endpoints healthy"
        return 0
    else
        log_error "✗ ${failed} API endpoint(s) failed"
        return 1
    fi
}

# ========================================
# Function: System Resources Monitoring
# ========================================
health_monitor_resources() {
    log_info "========================================="
    log_info "  System Resources Monitoring"
    log_info "========================================="

    # Docker stats (one-shot)
    if docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null; then
        :
    else
        log_warning "  ⚠️  Could not retrieve Docker stats"
    fi

    echo

    # Disk usage
    if command -v df &>/dev/null; then
        log_info "Disk Usage:"
        df -h / | awk 'NR==1 || /\/$/'
    fi

    echo
}

# ========================================
# Function: Comprehensive Health Report
# ========================================
health_report() {
    log_info "========================================="
    log_info "  Comprehensive Health Report"
    log_info "========================================="
    echo

    # Service health
    health_check_all_services
    echo

    # Database health
    health_check_database
    echo

    # Redis health
    health_check_redis
    echo

    # API endpoints
    health_check_api_endpoints
    echo

    # System resources
    health_monitor_resources
}

# ========================================
# Function: Continuous Health Monitoring
# ========================================
health_monitor_continuous() {
    local interval="${1:-60}"

    log_info "Starting continuous health monitoring (interval: ${interval}s)"
    log_info "Press Ctrl+C to stop"
    echo

    while true; do
        clear
        echo "=== Health Report at $(date) ==="
        echo

        health_check_all_services

        echo
        log_info "Next check in ${interval}s..."
        sleep "${interval}"
    done
}
