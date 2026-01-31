#!/bin/bash
set -e

BASE_URL="${1:-https://192.168.50.220}"
API_URL="${BASE_URL}:2542"
TEST_IP="192.168.99.99"
RESULTS=()
FAILED=0

red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }

log_test() {
    local name="$1" result="$2"
    if [ "$result" == "PASS" ]; then
        green "[PASS] $name"
        RESULTS+=("PASS: $name")
    else
        red "[FAIL] $name"
        RESULTS+=("FAIL: $name")
        ((FAILED++))
    fi
}

api() {
    curl -sk -X "$1" "$API_URL$2" -H "Content-Type: application/json" ${3:+-d "$3"} 2>/dev/null
}

echo "=========================================="
echo "Blacklist Platform E2E Test Suite"
echo "API: $API_URL | Frontend: $BASE_URL"
echo "=========================================="
echo ""

yellow "Test 1: Health Check"
HEALTH=$(api GET /health)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    log_test "API Health Check" "PASS"
else
    log_test "API Health Check" "FAIL"
fi

FRONTEND=$(curl -sk "$BASE_URL" 2>/dev/null | head -1)
if echo "$FRONTEND" | grep -q "<!DOCTYPE html>"; then
    log_test "Frontend Accessible" "PASS"
else
    log_test "Frontend Accessible" "FAIL"
fi
echo ""

yellow "Test 2: Blacklist CRUD"
ADD_RESULT=$(api POST /api/blacklist/manual-add "{\"ip_address\":\"$TEST_IP\",\"reason\":\"E2E Test\",\"source\":\"test\"}")
if echo "$ADD_RESULT" | grep -qE '"success"|"message"'; then
    log_test "Blacklist Add IP" "PASS"
else
    log_test "Blacklist Add IP" "FAIL"
fi

CHECK_RESULT=$(api GET "/api/blacklist/check?ip=$TEST_IP")
if echo "$CHECK_RESULT" | grep -q '"found":true\|"exists":true\|"is_blacklisted":true'; then
    log_test "Blacklist Check IP" "PASS"
else
    log_test "Blacklist Check IP" "FAIL"
fi

REMOVE_RESULT=$(api DELETE "/api/blacklist/remove/$TEST_IP")
if echo "$REMOVE_RESULT" | grep -qE '"success"|"removed"'; then
    log_test "Blacklist Remove IP" "PASS"
else
    log_test "Blacklist Remove IP" "FAIL"
fi
echo ""

yellow "Test 3: Dashboard Stats"
STATS=$(api GET /api/dashboard/stats)
if echo "$STATS" | grep -q '"total_ips"\|"active_ips"'; then
    log_test "Dashboard Stats" "PASS"
else
    log_test "Dashboard Stats" "FAIL"
fi
echo ""

yellow "Test 4: Whitelist Operations"
WL_ADD=$(api POST /api/ip-management/whitelist "{\"ip_address\":\"$TEST_IP\",\"reason\":\"E2E Whitelist Test\",\"source\":\"test\"}")
if echo "$WL_ADD" | grep -qE '"success"|"id"'; then
    log_test "Whitelist Add IP" "PASS"
else
    log_test "Whitelist Add IP" "FAIL"
fi

WL_LIST=$(api GET /api/ip-management/whitelist)
if echo "$WL_LIST" | grep -q "$TEST_IP"; then
    log_test "Whitelist List" "PASS"
    WL_ID=$(echo "$WL_LIST" | grep -o '"id":[0-9]*' | tail -1 | grep -o '[0-9]*')
    if [ -n "$WL_ID" ]; then
        WL_DEL=$(api DELETE "/api/ip-management/whitelist/$WL_ID")
        if echo "$WL_DEL" | grep -qE '"success"|"deleted"'; then
            log_test "Whitelist Delete" "PASS"
        else
            log_test "Whitelist Delete" "FAIL"
        fi
    fi
else
    log_test "Whitelist List" "FAIL"
fi
echo ""

yellow "Test 5: Batch Operations"
BATCH_ADD=$(api POST /api/blacklist/batch/add '{"ips":["10.99.1.1","10.99.1.2"],"reason":"Batch Test","source":"batch-test"}')
if echo "$BATCH_ADD" | grep -qE '"success"|"added"'; then
    log_test "Batch Add" "PASS"
else
    log_test "Batch Add" "FAIL"
fi

BATCH_RM=$(api POST /api/blacklist/batch/remove '{"ips":["10.99.1.1","10.99.1.2"]}')
if echo "$BATCH_RM" | grep -qE '"success"|"removed"'; then
    log_test "Batch Remove" "PASS"
else
    log_test "Batch Remove" "FAIL"
fi
echo ""

yellow "Test 6: Fortinet Integration"
FORTINET=$(api GET /api/fortinet/health)
if echo "$FORTINET" | grep -qE '"status"|"healthy"'; then
    log_test "Fortinet Health" "PASS"
else
    log_test "Fortinet Health" "FAIL"
fi

THREAT_FEED=$(curl -sk "$API_URL/api/fortinet/threat-feed" 2>/dev/null | head -c 100)
if [ -n "$THREAT_FEED" ]; then
    log_test "Fortinet Threat Feed" "PASS"
else
    log_test "Fortinet Threat Feed" "FAIL"
fi
echo ""

yellow "Test 7: Collection Status"
COLL_STATUS=$(api GET /api/collection/status)
if echo "$COLL_STATUS" | grep -qE '"status"|"service"'; then
    log_test "Collection Status" "PASS"
else
    log_test "Collection Status" "FAIL"
fi
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
TOTAL=${#RESULTS[@]}
PASSED=$((TOTAL - FAILED))
green "Passed: $PASSED / $TOTAL"
if [ $FAILED -gt 0 ]; then
    red "Failed: $FAILED"
    echo ""
    for r in "${RESULTS[@]}"; do
        if [[ "$r" == FAIL* ]]; then
            red "  $r"
        fi
    done
    exit 1
else
    green "All tests passed!"
    exit 0
fi
