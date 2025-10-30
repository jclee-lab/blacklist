#!/bin/bash
# Comprehensive Test Runner for Blacklist IP Management System
#
# Usage:
#   ./scripts/run-tests.sh              # Run all tests with coverage
#   ./scripts/run-tests.sh unit         # Run only unit tests
#   ./scripts/run-tests.sh security     # Run only security tests
#   ./scripts/run-tests.sh cache        # Run only cache tests
#   ./scripts/run-tests.sh integration  # Run only integration tests
#   ./scripts/run-tests.sh quick        # Run fast tests only
#   ./scripts/run-tests.sh coverage     # Generate coverage report

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Blacklist IP Management - Test Suite${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing dependencies...${NC}"
    pip install -r app/requirements.txt
fi

# Test mode (default: all)
TEST_MODE="${1:-all}"

case "$TEST_MODE" in
    unit)
        echo -e "${GREEN}🧪 Running UNIT tests only${NC}"
        pytest tests/unit/ -v --cov=app/core --cov-report=term-missing
        ;;

    security)
        echo -e "${YELLOW}🔒 Running SECURITY tests (SQL injection, CSRF, rate limiting)${NC}"
        pytest tests/security/ -v --cov=app/core/routes --cov=app/core/services
        ;;

    cache)
        echo -e "${BLUE}📦 Running CACHE tests (Redis integration)${NC}"
        pytest tests/unit/test_redis_cache.py -v
        ;;

    integration)
        echo -e "${GREEN}🔗 Running INTEGRATION tests${NC}"
        pytest tests/integration/ -v
        ;;

    api)
        echo -e "${GREEN}🌐 Running API tests${NC}"
        pytest tests/integration/test_api_comprehensive.py -v
        ;;

    quick)
        echo -e "${GREEN}⚡ Running QUICK tests (unit + cache)${NC}"
        pytest tests/unit/ tests/security/ -v -x --tb=short
        ;;

    coverage)
        echo -e "${GREEN}📊 Generating COVERAGE report${NC}"
        pytest tests/ --cov=app/core --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}✅ Coverage report generated: ${BLUE}htmlcov/index.html${NC}"
        ;;

    all|*)
        echo -e "${GREEN}🚀 Running ALL tests with coverage${NC}"
        echo ""

        # Run tests with coverage
        pytest tests/ -v \
            --cov=app/core \
            --cov-report=term-missing \
            --cov-report=html \
            --cov-report=json \
            --cov-fail-under=80

        TEST_RESULT=$?

        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

        if [ $TEST_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ All tests passed!${NC}"
            echo -e "${GREEN}✅ Coverage target (80%) met${NC}"
            echo ""
            echo -e "📊 Coverage report: ${BLUE}htmlcov/index.html${NC}"
        else
            echo -e "${RED}❌ Tests failed or coverage below 80%${NC}"
            echo ""
            echo -e "📊 Coverage report: ${BLUE}htmlcov/index.html${NC}"
            exit 1
        fi
        ;;
esac

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Test execution completed${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Show quick summary
if [ -f "coverage.json" ]; then
    COVERAGE=$(python3 -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}%\")" 2>/dev/null || echo "N/A")
    echo -e "📊 Total Coverage: ${GREEN}${COVERAGE}${NC}"
fi

echo ""
echo -e "${YELLOW}ℹ️  Test Categories:${NC}"
echo -e "  ${BLUE}unit${NC}         - Unit tests (fast, isolated)"
echo -e "  ${BLUE}security${NC}     - Security tests (SQL injection, CSRF, rate limiting)"
echo -e "  ${BLUE}cache${NC}        - Redis cache tests"
echo -e "  ${BLUE}integration${NC}  - Integration tests (API endpoints)"
echo -e "  ${BLUE}api${NC}          - API endpoint tests"
echo -e "  ${BLUE}quick${NC}        - Fast tests only"
echo -e "  ${BLUE}coverage${NC}     - Generate coverage report"
echo -e "  ${BLUE}all${NC}          - Run all tests (default)"
echo ""
