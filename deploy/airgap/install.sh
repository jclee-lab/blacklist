#!/bin/bash
set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log_step() { echo -e "\n${CYAN}===${NC} ${BOLD}$1${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGES_DIR="${SCRIPT_DIR}/images"

preflight_checks() {
    log_step "Preflight Checks"

    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed. Install Docker first: https://docs.docker.com/engine/install/"
    fi
    log_success "Docker $(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"

    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose not installed. Install Docker Compose plugin first."
    fi
    log_success "Docker Compose $(docker compose version --short)"

    if [ ! -d "${IMAGES_DIR}" ]; then
        log_error "images/ directory not found"
    fi

    local required_images=(
        "blacklist-app.tar.gz"
        "blacklist-collector.tar.gz"
        "blacklist-frontend.tar.gz"
        "blacklist-postgres.tar.gz"
        "blacklist-redis.tar.gz"
    )

    for img in "${required_images[@]}"; do
        if [ -f "${IMAGES_DIR}/${img}" ]; then
            log_success "${img} ($(du -h "${IMAGES_DIR}/${img}" | cut -f1))"
        else
            log_error "${img} not found"
        fi
    done

    if [ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
    fi
    log_success "docker-compose.yml"

    if [ -f "${IMAGES_DIR}/checksums.sha256" ]; then
        log_success "checksums.sha256"
    else
        log_warning "checksums.sha256 not found (integrity check will be skipped)"
    fi

    local available_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "${available_gb}" -lt 3 ]; then
        log_warning "Low disk space: ${available_gb}GB (recommend 3GB+)"
    else
        log_success "Disk space: ${available_gb}GB"
    fi

    for port in 443 2542 5432 6379 8545; do
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            log_warning "Port ${port} in use"
        fi
    done
}

verify_checksums() {
    log_step "Verify Image Integrity (SHA256)"

    if [ ! -f "${IMAGES_DIR}/checksums.sha256" ]; then
        log_warning "checksums.sha256 not found, skipping verification"
        return 0
    fi

    cd "${IMAGES_DIR}"
    if sha256sum -c checksums.sha256 --status 2>/dev/null; then
        log_success "All checksums verified"
    else
        log_info "Verifying individual files..."
        local failed=0
        while IFS='  ' read -r expected_hash filename; do
            if [ -f "$filename" ]; then
                actual_hash=$(sha256sum "$filename" | awk '{print $1}')
                if [ "$expected_hash" = "$actual_hash" ]; then
                    log_success "${filename}: OK"
                else
                    log_error "${filename}: CHECKSUM MISMATCH (corrupted or tampered)"
                    failed=1
                fi
            fi
        done < checksums.sha256
        if [ "$failed" -eq 1 ]; then
            log_error "Integrity check failed. Re-download the airgap package."
        fi
    fi
    cd "${SCRIPT_DIR}"
}

load_images() {
    log_step "Load Docker Images"

    local images=(
        "blacklist-app.tar.gz"
        "blacklist-collector.tar.gz"
        "blacklist-frontend.tar.gz"
        "blacklist-postgres.tar.gz"
        "blacklist-redis.tar.gz"
    )

    for img in "${images[@]}"; do
        local name="${img%.tar.gz}"
        log_info "Loading ${name}..."
        if gunzip -c "${IMAGES_DIR}/${img}" | docker load > /dev/null 2>&1; then
            log_success "${name}"
        else
            log_error "Failed to load ${name}"
        fi
    done

    log_success "All images loaded"
}

setup_secrets() {
    log_step "Setup Environment Secrets"

    local env_file="${SCRIPT_DIR}/.env"

    if [ -f "${env_file}" ]; then
        log_info ".env already exists, skipping secret generation"
        return 0
    fi

    if ! command -v openssl &> /dev/null; then
        log_warning "openssl not found, using /dev/urandom for secrets"
        local gen_secret="head -c 32 /dev/urandom | xxd -p | tr -d '\n'"
    else
        local gen_secret="openssl rand -hex 32"
    fi

    log_info "Generating secrets..."
    cat > "${env_file}" <<EOF
# Blacklist Platform Secrets (auto-generated)
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# WARNING: Keep this file secure. Do not commit to version control.

CREDENTIAL_MASTER_KEY=$(eval $gen_secret)
SECRET_KEY=$(eval $gen_secret)
CREDENTIAL_ENCRYPTION_KEY=$(eval $gen_secret)
EOF

    chmod 600 "${env_file}"
    log_success "Secrets generated (.env)"
    log_warning "Store .env securely - it contains encryption keys"
}

deploy_services() {
    log_step "Deploy Services"

    cd "${SCRIPT_DIR}"

    local containers="blacklist-app blacklist-collector blacklist-frontend blacklist-postgres blacklist-redis"
    for c in $containers; do
        if docker ps -aq -f "name=^${c}$" | grep -q .; then
            log_info "Removing existing container: ${c}..."
            docker rm -f "$c" 2>/dev/null || true
        fi
    done

    log_info "Starting services..."
    docker compose up -d 2>&1 | grep -v "^$" || true

    log_info "Waiting for services to initialize (30s)..."
    sleep 30

    log_success "Services started"
}

restore_database() {
    log_step "Restore Database"

    local dump_file="${IMAGES_DIR}/blacklist-db-dump.sql.gz"
    
    if [ ! -f "${dump_file}" ]; then
        log_warning "Database dump not found, skipping restore"
        return 0
    fi

    log_info "Waiting for PostgreSQL to be ready..."
    local retries=30
    while ! docker exec blacklist-postgres pg_isready -U postgres -q 2>/dev/null; do
        retries=$((retries - 1))
        if [ "$retries" -le 0 ]; then
            log_warning "PostgreSQL not ready, skipping restore"
            return 0
        fi
        sleep 1
    done

    log_info "Restoring database from dump..."
    if gunzip -c "${dump_file}" | docker exec -i blacklist-postgres psql -U postgres blacklist > /dev/null 2>&1; then
        log_success "Database restored successfully"
    else
        log_warning "Database restore had warnings (may be OK if tables exist)"
    fi
}

health_checks() {
    log_step "Health Checks"

    docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || docker compose ps

    local endpoints=(
        "http://localhost:2542/api/health|API"
        "http://localhost:8545/health|Collector"
    )

    echo ""
    for ep in "${endpoints[@]}"; do
        local url="${ep%|*}"
        local name="${ep#*|}"
        if curl -s "${url}" 2>/dev/null | grep -q "healthy\|status"; then
            log_success "${name}: healthy"
        else
            log_warning "${name}: not responding"
        fi
    done

    if curl -sk "https://localhost:443" > /dev/null 2>&1; then
        log_success "Frontend: accessible"
    else
        log_warning "Frontend: not responding"
    fi
}

post_install() {
    log_step "Installation Complete"

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Blacklist Platform Deployed Successfully                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Access Points:"
    echo "  Frontend:  https://localhost:443"
    echo "  API:       http://localhost:2542/api/health"
    echo "  Collector: http://localhost:8545/health"
    echo ""
    echo "Management:"
    echo "  Status:    docker compose ps"
    echo "  Logs:      docker compose logs -f"
    echo "  Stop:      docker compose down"
    echo "  Restart:   docker compose restart"
    echo ""
}

show_help() {
    echo "Blacklist Airgap Installer"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-load    Skip image loading (images already loaded)"
    echo "  --help, -h     Show this help"
    echo ""
}

main() {
    local skip_load=false

    for arg in "$@"; do
        case $arg in
            --skip-load) skip_load=true ;;
            --help|-h) show_help; exit 0 ;;
            *) log_warning "Unknown option: $arg" ;;
        esac
    done

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Blacklist Airgap Installer v1.0                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    preflight_checks
    verify_checksums

    if [ "$skip_load" = false ]; then
        load_images
    else
        log_info "Skipping image load (--skip-load)"
    fi


    setup_secrets

    deploy_services
    restore_database
    health_checks
    post_install

    log_success "Installation completed!"
}

main "$@"
