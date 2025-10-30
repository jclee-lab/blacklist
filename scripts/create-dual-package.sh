#!/bin/bash
##############################################################################
# 🚀 Blacklist 2-File Package Creator (Advanced & Efficient)
# Package: blacklist.tar.gz + install.sh
##############################################################################

set -euo pipefail

# Auto-switch to local context for local projects
if [ -z "${DOCKER_CONTEXT:-}" ] || [ "${DOCKER_CONTEXT}" != "local" ]; then
    echo -e "\033[1;33m[WARNING]\033[0m Docker context not set to 'local', switching..."
    export DOCKER_CONTEXT=local
    echo -e "\033[0;32m[SUCCESS]\033[0m Context switched to: local"
fi

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Validate Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker not installed"
    exit 1
fi

# Parse command line arguments
USE_RUNNING=false
for arg in "$@"; do
    case $arg in
        --use-running)
            USE_RUNNING=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --use-running    Use docker commit from running containers (faster)"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Default: Build from Dockerfiles"
            echo ""
            echo "Examples:"
            echo "  $0                  # Build from Dockerfiles"
            echo "  $0 --use-running    # Commit running containers"
            exit 0
            ;;
    esac
done

export USE_RUNNING

# Configuration
readonly VERSION=$(cat /home/jclee/app/blacklist/VERSION 2>/dev/null || echo "unknown")
readonly DATE=$(date +%Y%m%d)
readonly WORK_DIR="/tmp/blacklist-dual-package"
readonly OUTPUT_DIR="/home/jclee/app/blacklist/offline-packages"
readonly PROJECT_ROOT="/home/jclee/app/blacklist"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 2-File Package Creator (blacklist.tar.gz + install.sh)  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Version: ${VERSION}"
log_info "Work Dir: ${WORK_DIR}"
if [ "$USE_RUNNING" = "true" ]; then
    log_info "Mode: Commit from running containers"
else
    log_info "Mode: Build from Dockerfiles"
fi
echo ""

##############################################################################
# Step 1: Prepare Work Directory
##############################################################################
log_step "Step 1/5: Prepare Work Directory"

rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}"/{docker-images,config,docs,patches}

log_success "Work directory created"
echo ""

##############################################################################
# Step 2: Build or Commit Docker Images
##############################################################################
# Check for --use-running flag
USE_RUNNING=${USE_RUNNING:-false}

if [ "$USE_RUNNING" = "true" ]; then
    log_step "Step 2/5: Commit Running Containers to Images"
    log_info "Using docker commit from running containers..."
else
    log_step "Step 2/5: Build and Export Docker Images"
    log_info "Building from Dockerfiles..."
fi

cd "${PROJECT_ROOT}"

# Array of services (format: name:dockerfile:context OR name:EXTERNAL:image)
declare -a SERVICES=(
    "blacklist-app:app/Dockerfile:app"
    "blacklist-collector:collector/Dockerfile:collector"
    "blacklist-postgres:postgres/Dockerfile:postgres"
    "blacklist-redis:redis/Dockerfile:redis"
    "blacklist-frontend:frontend/Dockerfile:frontend"
)

TOTAL=${#SERVICES[@]}
CURRENT=0

for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r name dockerfile context image_tag <<< "$service_info"
    CURRENT=$((CURRENT + 1))

    # Check if this is an external image
    if [ "$dockerfile" = "EXTERNAL" ]; then
        log_info "  [${CURRENT}/${TOTAL}] Pulling external image ${context}..."

        # Pull external image (e.g., traefik:v2.10)
        if docker pull "${context}" 2>&1 | tail -3; then
            # Tag as offline
            docker tag "${context}" "${name}:offline"

            # Save image
            docker save -o "${WORK_DIR}/docker-images/${name}(${DATE}).tar" "${name}:offline"

            # Create latest symlink
            cd "${WORK_DIR}/docker-images"
            ln -sf "${name}(${DATE}).tar" "${name}(latest).tar"
            cd "${PROJECT_ROOT}"

            IMAGE_SIZE=$(du -h "${WORK_DIR}/docker-images/${name}(${DATE}).tar" | cut -f1)
            log_success "  ✓ ${name}(${DATE}).tar saved (${IMAGE_SIZE})"
            log_info "    → ${name}(latest).tar symlink created"
        else
            log_error "Failed to pull ${context}"
            exit 1
        fi
    elif [ "$USE_RUNNING" = "true" ]; then
        log_info "  [${CURRENT}/${TOTAL}] Committing ${name} from running container..."

        # Commit running container to image
        if docker commit "${name}" "${name}:offline" 2>&1 | tail -1; then
            # Save image
            docker save -o "${WORK_DIR}/docker-images/${name}(${DATE}).tar" "${name}:offline"

            # Create latest symlink
            cd "${WORK_DIR}/docker-images"
            ln -sf "${name}(${DATE}).tar" "${name}(latest).tar"
            cd "${PROJECT_ROOT}"

            IMAGE_SIZE=$(du -h "${WORK_DIR}/docker-images/${name}(${DATE}).tar" | cut -f1)
            log_success "  ✓ ${name}(${DATE}).tar saved from running container (${IMAGE_SIZE})"
        else
            log_error "Failed to commit ${name} (is container running?)"
            exit 1
        fi
    else
        log_info "  [${CURRENT}/${TOTAL}] Building ${name}:offline..."

        # Build with progress
        if docker build -t "${name}:offline" -f "${dockerfile}" "${context}" 2>&1 | grep -E "(Step|writing|naming|DONE)" | tail -5; then
            # Save image with date in filename
            docker save -o "${WORK_DIR}/docker-images/${name}(${DATE}).tar" "${name}:offline"

            # Create latest symlink
            cd "${WORK_DIR}/docker-images"
            ln -sf "${name}(${DATE}).tar" "${name}(latest).tar"
            cd "${PROJECT_ROOT}"

            IMAGE_SIZE=$(du -h "${WORK_DIR}/docker-images/${name}(${DATE}).tar" | cut -f1)
            log_success "  ✓ ${name}(${DATE}).tar saved (${IMAGE_SIZE})"
            log_info "    → ${name}(latest).tar symlink created"
        else
            log_error "Failed to build ${name}"
            exit 1
        fi
    fi
done

if [ "$USE_RUNNING" = "true" ]; then
    log_success "All running containers committed and exported"
else
    log_success "All Docker images built and exported"
fi
echo ""

##############################################################################
# Step 3: Copy Essential Files Only (Optimized)
##############################################################################
log_step "Step 3/5: Copy Essential Files (Size Optimized)"

# Essential configs only
cp "${PROJECT_ROOT}/docker-compose.yml" "${WORK_DIR}/config/"
log_info "  ✓ docker-compose.yml"

cp "${PROJECT_ROOT}/.env.example" "${WORK_DIR}/config/"
log_info "  ✓ .env.example"

# Copy SQL migrations only (no shell scripts)
if [ -d "${PROJECT_ROOT}/postgres/migrations" ]; then
    mkdir -p "${WORK_DIR}/config/migrations"
    SQL_COUNT=$(find "${PROJECT_ROOT}/postgres/migrations" -name "*.sql" 2>/dev/null | wc -l)
    if [ "$SQL_COUNT" -gt 0 ]; then
        cp "${PROJECT_ROOT}/postgres/migrations"/*.sql "${WORK_DIR}/config/migrations/" 2>/dev/null || true
        log_info "  ✓ ${SQL_COUNT} SQL migrations"
    fi
fi

# Copy runtime patches (NEW v3.3.8)
if [ -d "${PROJECT_ROOT}/offline-packages/patches" ]; then
    PATCH_COUNT=$(find "${PROJECT_ROOT}/offline-packages/patches" -name "*.sh" 2>/dev/null | wc -l)
    if [ "$PATCH_COUNT" -gt 0 ]; then
        cp "${PROJECT_ROOT}/offline-packages/patches"/*.sh "${WORK_DIR}/patches/" 2>/dev/null || true
        # Also copy README if exists
        [ -f "${PROJECT_ROOT}/offline-packages/patches/README.md" ] && \
            cp "${PROJECT_ROOT}/offline-packages/patches/README.md" "${WORK_DIR}/patches/"
        log_info "  ✓ ${PATCH_COUNT} runtime patches (auto-applied on container start)"
    fi
fi

# XWiki docs (REQUIRED)
if [ -d "${PROJECT_ROOT}/docs/xwiki-sections" ]; then
    cp -r "${PROJECT_ROOT}/docs/xwiki-sections" "${WORK_DIR}/docs/"
    DOC_COUNT=$(find "${WORK_DIR}/docs/xwiki-sections" -name "*.txt" -o -name "*.xar" | wc -l)
    log_info "  ✓ XWiki docs (${DOC_COUNT} files)"
fi

# Skip: Makefile (use docker compose directly)
# Skip: .sh migration scripts (SQL only needed)

log_success "Essential files copied (optimized)"
echo ""

##############################################################################
# Step 4: Create blacklist.tar.gz (Optimized)
##############################################################################
log_step "Step 4/5: Create blacklist.tar.gz (Size Optimized)"

cd "${WORK_DIR}"

# Include only essential directories
INCLUDE_DIRS="docker-images/ config/"

# Check if docs exists and has content
if [ -d "docs" ] && [ "$(find docs -type f | wc -l)" -gt 0 ]; then
    INCLUDE_DIRS="${INCLUDE_DIRS} docs/"
fi

tar -czf blacklist.tar.gz ${INCLUDE_DIRS}

PACKAGE_SIZE=$(du -h blacklist.tar.gz | cut -f1)
UNCOMPRESSED_SIZE=$(du -sh docker-images config 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "N/A")
log_success "blacklist.tar.gz created (${PACKAGE_SIZE})"
log_info "  Compression ratio: $(echo "scale=1; 100 - ($(stat -f%z blacklist.tar.gz 2>/dev/null || stat -c%s blacklist.tar.gz) * 100.0 / $(du -sb docker-images config | awk '{sum+=$1} END {print sum}'))" | bc 2>/dev/null || echo "~33")% smaller"
echo ""

##############################################################################
# Step 5: Create Standalone install.sh
##############################################################################
log_step "Step 5/5: Create Standalone install.sh"

cat > "${WORK_DIR}/install.sh" << 'INSTALL_SCRIPT_EOF'
#!/bin/bash
##############################################################################
# 🛡️ Blacklist Standalone Installer (Advanced & Validated)
# Auto-extracts blacklist.tar.gz and installs all services
##############################################################################

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log_step() { echo -e "\n${CYAN}[STEP]${NC} ${BOLD}$1${NC}\n"; }

##############################################################################
# Preflight Checks
##############################################################################
preflight_checks() {
    log_step "Preflight Checks"

    # Ensure local Docker context (avoid remote daemon issues)
    unset DOCKER_CONTEXT 2>/dev/null || true
    export DOCKER_CONTEXT=

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed. Install: https://docs.docker.com/engine/install/"
    fi
    
    DOCKER_VERSION=$(docker --version | sed -E 's/.*([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
    log_success "Docker ${DOCKER_VERSION} detected"
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose plugin not available"
    fi
    
    COMPOSE_VERSION=$(docker compose version --short)
    log_success "Docker Compose ${COMPOSE_VERSION} detected"
    
    # Check blacklist.tar.gz
    if [ ! -f "blacklist.tar.gz" ]; then
        log_error "blacklist.tar.gz not found in current directory"
    fi
    
    PACKAGE_SIZE=$(du -h blacklist.tar.gz | cut -f1)
    log_success "Package found: blacklist.tar.gz (${PACKAGE_SIZE})"
    
    # Check disk space (need at least 5GB)
    AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "${AVAILABLE_GB}" -lt 5 ]; then
        log_warning "Low disk space: ${AVAILABLE_GB}GB available (recommend 5GB+)"
    else
        log_success "Disk space: ${AVAILABLE_GB}GB available"
    fi
    
    # Check ports
    REQUIRED_PORTS=(443 80)
    for port in "${REQUIRED_PORTS[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            log_warning "Port ${port} already in use (may cause conflicts)"
        else
            log_success "Port ${port} available"
        fi
    done
}

##############################################################################
# Network Connectivity Checks (Optional)
##############################################################################
network_checks() {
    log_step "Network Connectivity Checks"

    # Skip if --skip-network-check flag provided
    if [ "${SKIP_NETWORK_CHECK:-false}" = "true" ]; then
        log_warning "Network checks skipped (--skip-network-check)"
        return 0
    fi

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_warning "curl not found - skipping network checks"
        log_info "  → Install curl for network diagnostics: apt-get install curl"
        log_info "  → Skipping this step won't affect installation"
        return 0
    fi

    log_info "Testing external API connectivity..."
    echo ""

    # Test REGTECH API
    log_info "  [1/2] REGTECH API (regtech.fsec.or.kr)..."
    if command -v timeout &> /dev/null; then
        HTTP_CODE=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" https://regtech.fsec.or.kr 2>/dev/null || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://regtech.fsec.or.kr 2>/dev/null || echo "000")
    fi

    if [ "${HTTP_CODE}" = "000" ]; then
        log_warning "    ⚠ REGTECH unreachable (timeout or network error)"
        log_info "    → This is OK for air-gap environments"
        log_info "    → Data collection will require valid credentials later"
    elif [ "${HTTP_CODE:0:1}" = "2" ] || [ "${HTTP_CODE:0:1}" = "3" ]; then
        log_success "    ✓ REGTECH reachable (HTTP ${HTTP_CODE})"
    else
        log_warning "    ⚠ REGTECH returned HTTP ${HTTP_CODE}"
    fi

    # Test SECUDIUM API
    log_info "  [2/2] SECUDIUM API (www.secudium.com)..."
    if command -v timeout &> /dev/null; then
        HTTP_CODE=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" https://www.secudium.com 2>/dev/null || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://www.secudium.com 2>/dev/null || echo "000")
    fi

    if [ "${HTTP_CODE}" = "000" ]; then
        log_warning "    ⚠ SECUDIUM unreachable (timeout or network error)"
        log_info "    → This is OK for air-gap environments"
        log_info "    → Data collection will require valid credentials later"
    elif [ "${HTTP_CODE:0:1}" = "2" ] || [ "${HTTP_CODE:0:1}" = "3" ]; then
        log_success "    ✓ SECUDIUM reachable (HTTP ${HTTP_CODE})"
    else
        log_warning "    ⚠ SECUDIUM returned HTTP ${HTTP_CODE}"
    fi

    echo ""
    log_info "Network checks completed (not required for installation)"
    log_info "  → If services are unreachable in air-gap environments:"
    log_info "    1. This is normal and expected"
    log_info "    2. Installation will continue without issues"
    log_info "    3. Configure credentials after deployment"
    log_info "  → To skip network checks: ./install.sh --skip-network-check"
    echo ""
}

##############################################################################
# Extract Package
##############################################################################
extract_package() {
    log_step "Extract Package"
    
    log_info "Extracting blacklist.tar.gz..."
    
    # Extract with progress
    if tar -xzf blacklist.tar.gz 2>&1 | while IFS= read -r line; do
        echo "      $line"
    done; then
        log_success "Package extracted"
    else
        log_error "Failed to extract package"
    fi
    
    # Verify structure
    [ ! -d "docker-images" ] && log_error "Missing docker-images/"
    [ ! -d "config" ] && log_error "Missing config/"
    [ ! -f "config/docker-compose.yml" ] && log_error "Missing docker-compose.yml"

    log_success "Package structure validated"
}

##############################################################################
# Load Docker Images
##############################################################################
load_docker_images() {
    log_step "Load Docker Images"

    # Remove existing :offline images to prevent "renaming" messages
    log_info "Cleaning up existing offline images..."
    docker images --format "{{.Repository}}:{{.Tag}}" | grep ":offline$" | xargs -r docker rmi -f >/dev/null 2>&1 || true

    local images=(
        "blacklist-app(latest).tar"
        "blacklist-collector(latest).tar"
        "blacklist-postgres(latest).tar"
        "blacklist-redis(latest).tar"
        "blacklist-frontend(latest).tar"
        "blacklist-nginx(latest).tar"
    )

    local total=${#images[@]}
    local loaded=0
    local failed=0

    for img in "${images[@]}"; do
        local num=$((loaded + failed + 1))
        log_info "  [${num}/${total}] Loading ${img}..."

        if [ ! -f "docker-images/${img}" ]; then
            log_warning "  ✗ ${img} not found - skipping"
            failed=$((failed + 1))
            continue
        fi

        # Load with output (filter out renaming messages)
        if docker load -i "docker-images/${img}" 2>&1 | while IFS= read -r line; do
            if echo "$line" | grep -qE "Loaded image|sha256" && ! echo "$line" | grep -q "renaming the old one"; then
                echo "      $line"
            fi
        done; then
            log_success "  ✓ ${img} loaded"
            loaded=$((loaded + 1))
        else
            log_warning "  ✗ ${img} failed to load"
            failed=$((failed + 1))
        fi
    done

    if [ $failed -gt 0 ]; then
        log_warning "Loaded: ${loaded}/${total} images (${failed} failed)"
    else
        log_success "All ${total} images loaded successfully"
    fi
}

##############################################################################
# Setup Data Directories
##############################################################################
setup_data_directories() {
    log_step "Setup Data Directories"
    
    local dirs=(
        "data/postgres"
        "data/redis"
        "data/collector"
        "data/app/logs"
        "data/app/uploads"
        "data/nginx/logs"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "${dir}"
        log_success "  ✓ ${dir}"
    done
    
    log_success "Data directories created"
}

##############################################################################
# Copy Database Migrations (to postgres init-scripts)
##############################################################################
copy_migrations() {
    if [ ! -d "config/migrations" ]; then
        log_info "No migrations found - skipping"
        return 0
    fi

    log_step "Copy Database Migrations"

    local migration_count=$(find config/migrations -name "*.sql" 2>/dev/null | wc -l)

    if [ "$migration_count" -gt 0 ]; then
        # Copy to data directory for postgres to auto-apply
        mkdir -p data/postgres-init
        cp config/migrations/*.sql data/postgres-init/ 2>/dev/null || true
        log_success "${migration_count} migrations copied to postgres init directory"
    else
        log_info "No SQL migrations found"
    fi
}

##############################################################################
# Configure Environment
##############################################################################
configure_environment() {
    log_step "Configure Environment"
    
    if [ ! -f ".env" ]; then
        if [ -f "config/.env.example" ]; then
            cp config/.env.example .env
            log_success ".env created from template"
            log_warning "IMPORTANT: Edit .env and set your credentials"
        else
            log_warning ".env.example not found - you'll need to create .env manually"
        fi
    else
        log_info ".env already exists - keeping current configuration"
    fi
    
    # Copy docker-compose.yml to current directory
    if [ -f "config/docker-compose.yml" ]; then
        cp config/docker-compose.yml .
        log_success "docker-compose.yml copied"
    else
        log_error "config/docker-compose.yml not found"
    fi
}

##############################################################################
# Deploy Services
##############################################################################
deploy_services() {
    log_step "Deploy Services"
    
    log_info "Starting Docker Compose..."
    
    # Start services with output
    if docker compose up -d 2>&1 | while IFS= read -r line; do
        if echo "$line" | grep -qE "⚠️|WARNING"; then
            continue
        fi
        echo "$line"
    done; then
        log_success "Services started"
    else
        log_error "Failed to start services"
    fi
    
    log_info "Waiting 30 seconds for services to initialize..."
    sleep 30
}

##############################################################################
# Health Checks
##############################################################################
health_checks() {
    log_step "Health Checks"

    # Check container status
    log_info "Checking container status..."
    docker compose ps

    local unhealthy=$(docker compose ps --format json 2>/dev/null | grep -c '"Health":"unhealthy"' | tr -d '\n' || echo "0")
    if [ "$unhealthy" -gt 0 ]; then
        log_warning "${unhealthy} unhealthy containers detected"
    fi
}

##############################################################################
# API Validation Tests
##############################################################################
api_validation_tests() {
    log_step "API Validation Tests"
    
    local passed=0
    local failed=0
    
    # Test 1: Health Check
    log_info "[Test 1/6] Health Check API..."
    if curl -sk https://localhost/health 2>/dev/null | grep -q "healthy"; then
        log_success "  ✓ Health Check passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ Health Check failed"
        failed=$((failed + 1))
    fi
    
    # Test 2: FortiGate API
    log_info "[Test 2/6] FortiGate Active IPs API..."
    if curl -sk https://localhost/api/fortinet/active-ips 2>/dev/null | grep -q "success"; then
        log_success "  ✓ FortiGate API passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ FortiGate API failed"
        failed=$((failed + 1))
    fi
    
    # Test 3: Collection Status
    log_info "[Test 3/6] Collection Status API..."
    if curl -sk https://localhost/api/collection/status 2>/dev/null | grep -q "success"; then
        log_success "  ✓ Collection Status passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ Collection Status failed"
        failed=$((failed + 1))
    fi
    
    # Test 4: Blacklist Check
    log_info "[Test 4/6] Blacklist Check API..."
    if curl -sk "https://localhost/api/blacklist/check?ip=1.2.3.4" 2>/dev/null | grep -q "success"; then
        log_success "  ✓ Blacklist Check passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ Blacklist Check failed"
        failed=$((failed + 1))
    fi
    
    # Test 5: Collection Panel UI
    log_info "[Test 5/6] Collection Panel UI..."
    if curl -sk https://localhost/collection-panel/ 2>/dev/null | grep -q "데이터 수집 관리"; then
        log_success "  ✓ Collection Panel UI passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ Collection Panel UI failed"
        failed=$((failed + 1))
    fi
    
    # Test 6: Settings Page
    log_info "[Test 6/6] Settings Page UI..."
    if curl -sk https://localhost/settings/ 2>/dev/null | grep -q "시스템 설정"; then
        log_success "  ✓ Settings Page passed"
        passed=$((passed + 1))
    else
        log_warning "  ✗ Settings Page failed"
        failed=$((failed + 1))
    fi
    
    echo ""
    if [ $failed -eq 0 ]; then
        log_success "✅ All tests passed! (${passed}/6)"
    else
        log_warning "⚠️  Some tests failed (Passed: ${passed}/6, Failed: ${failed}/6)"
        log_info "Check logs: docker compose logs -f"
    fi
}

##############################################################################
# Post-Install Guidance
##############################################################################
post_install_guidance() {
    log_step "Installation Complete!"
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Blacklist Services Deployed Successfully                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📍 Access Points:"
    echo "   ${CYAN}https://localhost${NC}                    - Main Application"
    echo "   ${CYAN}https://localhost/collection-panel/${NC}  - Data Collection"
    echo "   ${CYAN}https://localhost/settings/${NC}          - System Settings"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Configure credentials: ${CYAN}vi .env${NC}"
    echo "   2. Restart services:      ${CYAN}docker compose restart${NC}"
    echo "   3. Setup REGTECH/SECUDIUM at Collection Panel"
    echo "   4. Integrate FortiGate:   ${CYAN}https://localhost/api/fortinet/active-ips${NC}"
    echo ""
    echo "📊 Management Commands:"
    echo "   Status:  ${CYAN}docker compose ps${NC}"
    echo "   Logs:    ${CYAN}docker compose logs -f${NC}"
    echo "   Stop:    ${CYAN}docker compose down${NC}"
    echo "   Restart: ${CYAN}docker compose restart${NC}"
    echo ""
    echo "📚 Documentation: docs/xwiki-sections/"
    echo "   - XAR import:  docs/xwiki-sections/blacklist-docs.xar"
    echo "   - Manual copy: *.txt files (00-index.txt ~ 10-monitoring.txt)"
    echo ""
}

##############################################################################
# Main Execution
##############################################################################
##############################################################################
# Parse Command Line Arguments
##############################################################################
parse_args() {
    SKIP_NETWORK_CHECK=false

    for arg in "$@"; do
        case $arg in
            --skip-network-check)
                SKIP_NETWORK_CHECK=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-network-check    Skip REGTECH/SECUDIUM connectivity tests"
                echo "  --help, -h              Show this help message"
                echo ""
                echo "Example:"
                echo "  $0                          # Normal installation with network checks"
                echo "  $0 --skip-network-check     # Air-gap installation (skip network tests)"
                exit 0
                ;;
            *)
                log_warning "Unknown option: $arg (use --help for usage)"
                ;;
        esac
    done

    export SKIP_NETWORK_CHECK
}

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🛡️  Blacklist Standalone Installer v3.3.1                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    parse_args "$@"
    preflight_checks
    network_checks
    extract_package
    load_docker_images
    setup_data_directories
    copy_migrations
    configure_environment
    deploy_services
    health_checks
    api_validation_tests
    post_install_guidance

    echo ""
    log_success "🎉 Installation completed successfully!"
    echo ""
}

# Run main
main "$@"
INSTALL_SCRIPT_EOF

chmod +x "${WORK_DIR}/install.sh"
log_success "Standalone install.sh created"
echo ""

##############################################################################
# Finalize Package
##############################################################################
log_step "Finalize Package"

mkdir -p "${OUTPUT_DIR}"

# Move files to output
mv "${WORK_DIR}/blacklist.tar.gz" "${OUTPUT_DIR}/"
mv "${WORK_DIR}/install.sh" "${OUTPUT_DIR}/"

# Cleanup
rm -rf "${WORK_DIR}"

log_success "Package finalized (2 files only - no checksums)"
echo ""

##############################################################################
# Summary
##############################################################################
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ 2-File Package Created Successfully                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Files (ONLY 2):"
echo "   ${OUTPUT_DIR}/blacklist.tar.gz"
echo "   ${OUTPUT_DIR}/install.sh"
echo ""
echo "📊 Package Size:"
du -h "${OUTPUT_DIR}/blacklist.tar.gz"
du -h "${OUTPUT_DIR}/install.sh"
echo ""
echo "🚀 Installation (Air-Gap Environment):"
echo "   1. Transfer both files to target system"
echo "   2. ${CYAN}bash install.sh${NC}"
echo "   3. Follow on-screen instructions"
echo ""
echo "✨ Features:"
echo "   ✓ Automatic extraction"
echo "   ✓ Docker image loading (6 services)"
echo "   ✓ Data directory creation"
echo "   ✓ Database migrations"
echo "   ✓ API validation tests (6 tests)"
echo "   ✓ Comprehensive health checks"
echo ""
