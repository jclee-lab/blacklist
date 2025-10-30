#!/bin/bash
# Package Integrity Verification Script - Phase 2 Implementation
#
# Purpose: Automated post-extraction validation of offline packages
# Usage: bash scripts/verify-package-integrity.sh <package-directory>
#
# Created: 2025-10-22
# Phase: 2.2 - Automated Integrity Checks

set -euo pipefail

# ========================================
# Color Output Functions
# ========================================
log_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# ========================================
# Variables
# ========================================
PACKAGE_DIR="${1:-.}"
TEST_RESULTS=()
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# ========================================
# Test Runner Function
# ========================================
run_test() {
    local test_name="$1"
    local test_command="$2"
    local critical="${3:-false}"  # Default non-critical

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log_info "[Test ${TESTS_TOTAL}] ${test_name}"

    if eval "${test_command}"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "  ✓ PASS"
        TEST_RESULTS+=("✅ ${test_name}")
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        if [ "${critical}" = "true" ]; then
            log_error "  ✗ FAIL (CRITICAL)"
            TEST_RESULTS+=("❌ ${test_name} (CRITICAL)")
            return 1
        else
            log_warning "  ⚠ FAIL (Non-critical)"
            TEST_RESULTS+=("⚠️  ${test_name} (Non-critical)")
            return 0
        fi
    fi
}

# ========================================
# Header
# ========================================
echo
log_info "========================================="
log_info "  Package Integrity Verification (Phase 2)"
log_info "========================================="
log_info "Package Directory: ${PACKAGE_DIR}"
echo

# Change to package directory
cd "${PACKAGE_DIR}" || {
    log_error "Failed to access package directory: ${PACKAGE_DIR}"
    exit 1
}

# ========================================
# Test 1: Directory Structure
# ========================================
run_test "Directory structure complete" \
    "[ -d 'docker-images' ] && [ -d 'dependencies' ] && [ -d 'source' ] && [ -d 'scripts' ]" \
    "true"

# ========================================
# Test 2: Security - .env Exclusion
# ========================================
run_test ".env file excluded (CRITICAL SECURITY)" \
    "[ ! -f 'source/.env' ]" \
    "true"

# ========================================
# Test 3: VERSION File
# ========================================
run_test "VERSION file exists" \
    "[ -f 'source/VERSION' ] && [ -s 'source/VERSION' ]" \
    "true"

if [ -f "source/VERSION" ]; then
    VERSION_CONTENT=$(cat source/VERSION)
    log_info "  Version: ${VERSION_CONTENT}"
fi

# ========================================
# Test 4: SECUDIUM Credentials Template
# ========================================
run_test "SECUDIUM credentials in .env.example" \
    "grep -q 'SECUDIUM_ID' source/.env.example && grep -q 'SECUDIUM_PW' source/.env.example" \
    "false"

# ========================================
# Test 5: Docker Images
# ========================================
EXPECTED_IMAGES=(
    "blacklist-app.tar"
    "blacklist-collector.tar"
    "blacklist-postgres.tar"
    "blacklist-redis.tar"
    "blacklist-frontend.tar"
    "blacklist-nginx.tar"
)

run_test "All 6 Docker images present" \
    "ls docker-images/blacklist-app.tar docker-images/blacklist-collector.tar docker-images/blacklist-postgres.tar docker-images/blacklist-redis.tar docker-images/blacklist-frontend.tar docker-images/blacklist-nginx.tar &>/dev/null" \
    "true"

# Check image sizes
if [ -d "docker-images" ]; then
    TOTAL_IMAGE_SIZE=$(du -sh docker-images/ | awk '{print $1}')
    log_info "  Total Docker images size: ${TOTAL_IMAGE_SIZE}"
fi

# ========================================
# Test 6: Python Dependencies
# ========================================
run_test "Python dependencies packaged" \
    "[ -d 'dependencies/python' ] && [ $(find dependencies/python -name '*.whl' | wc -l) -gt 100 ]" \
    "true"

if [ -d "dependencies/python" ]; then
    PYTHON_PKG_COUNT=$(find dependencies/python -name '*.whl' | wc -l)
    log_info "  Python packages: ${PYTHON_PKG_COUNT}"
fi

# ========================================
# Test 7: Source Code Structure
# ========================================
run_test "Source code complete (6 core directories)" \
    "[ -d 'source/app' ] && [ -d 'source/collector' ] && [ -d 'source/postgres' ] && [ -d 'source/redis' ] && [ -d 'source/frontend' ] && [ -d 'source/nginx' ]" \
    "true"

# ========================================
# Test 8: Installation Scripts
# ========================================
run_test "Installation scripts present" \
    "[ -f 'install.sh' ] && [ -x 'install.sh' ] && [ -d 'scripts' ] && [ $(ls -1 scripts/*.sh 2>/dev/null | wc -l) -ge 5 ]" \
    "true"

if [ -d "scripts" ]; then
    SCRIPT_COUNT=$(ls -1 scripts/*.sh 2>/dev/null | wc -l || echo "0")
    log_info "  Installation scripts: ${SCRIPT_COUNT}"
fi

# ========================================
# Test 9: Package Size Validation
# ========================================
run_test "Package size within expected range" \
    "TOTAL_SIZE=$(du -sb . | awk '{print $1}'); [ ${TOTAL_SIZE} -gt 1000000000 ] && [ ${TOTAL_SIZE} -lt 3000000000 ]" \
    "false"

if [ -d "." ]; then
    TOTAL_SIZE_HR=$(du -sh . | awk '{print $1}')
    log_info "  Total package size: ${TOTAL_SIZE_HR}"
fi

# ========================================
# Test 10: PACKAGE_INFO.json (Optional)
# ========================================
run_test "PACKAGE_INFO.json present (optional)" \
    "[ -f 'PACKAGE_INFO.json' ]" \
    "false"

if [ -f "PACKAGE_INFO.json" ]; then
    log_info "  PACKAGE_INFO.json found - validating JSON syntax"
    if jq empty PACKAGE_INFO.json 2>/dev/null; then
        log_success "  ✓ Valid JSON syntax"
    else
        log_warning "  ⚠️  Invalid JSON syntax"
    fi
fi

# ========================================
# Test 11: Documentation Files
# ========================================
run_test "Documentation files present" \
    "[ -f 'README.md' ] && [ -d 'docs' ]" \
    "false"

if [ -d "docs" ]; then
    DOC_COUNT=$(find docs -type f | wc -l)
    log_info "  Documentation files: ${DOC_COUNT}"
fi

# ========================================
# Test 12: XWiki Templates (If available)
# ========================================
run_test "XWiki templates included (optional)" \
    "[ -d 'docs/xwiki-sections' ] && [ $(ls -1 docs/xwiki-sections/*.txt 2>/dev/null | wc -l) -gt 10 ]" \
    "false"

# ========================================
# Results Summary
# ========================================
echo
log_info "========================================="
log_info "  Verification Results"
log_info "========================================="

for result in "${TEST_RESULTS[@]}"; do
    echo "  ${result}"
done

echo
log_info "Tests Run: ${TESTS_TOTAL}"
log_success "Passed: ${TESTS_PASSED}"

if [ "${TESTS_FAILED}" -gt 0 ]; then
    log_error "Failed: ${TESTS_FAILED}"
else
    log_success "Failed: ${TESTS_FAILED}"
fi

SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_TOTAL))
log_info "Success Rate: ${SUCCESS_RATE}%"

echo
if [ "${TESTS_FAILED}" -eq 0 ] && [ "${TESTS_PASSED}" -eq "${TESTS_TOTAL}" ]; then
    log_success "========================================="
    log_success "  ✅ ALL TESTS PASSED - PACKAGE VERIFIED"
    log_success "========================================="
    exit 0
elif [ "${SUCCESS_RATE}" -ge 80 ]; then
    log_success "========================================="
    log_success "  ⚠️  PACKAGE FUNCTIONAL (${SUCCESS_RATE}% passed)"
    log_success "========================================="
    exit 0
else
    log_error "========================================="
    log_error "  ❌ PACKAGE VERIFICATION FAILED"
    log_error "========================================="
    exit 1
fi
