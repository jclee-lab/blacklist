#!/bin/bash

# Blacklist Production Environment Test Script (Shell version)

# --- Configuration ---
BASE_URL="http://blacklist-app:2542"
SUCCESS_COLOR='\033[92m'
FAIL_COLOR='\033[91m'
INFO_COLOR='\033[94m'
RESET_COLOR='\033[0m'

# --- Helper Functions ---
print_step() {
    echo -e "\n${INFO_COLOR}▶ $1${RESET_COLOR}"
}

print_success() {
    echo -e "${SUCCESS_COLOR}✅ $1${RESET_COLOR}"
}

print_fail() {
    echo -e "${FAIL_COLOR}❌ $1${RESET_COLOR}"
}

run_test() {
    local description="$1"
    local command="$2"
    
    echo -n "  - ${description}... "

    # Execute the command and capture the output and exit code
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${SUCCESS_COLOR}PASS${RESET_COLOR}"
        return 0
    else
        echo -e "${FAIL_COLOR}FAIL${RESET_COLOR}"
        print_fail "    Reason: $output"
        return 1
    fi
}

# --- Test Commands ---

# Usage: test_set_credentials <username> <password>
test_set_credentials() {
    local user="$1"
    local pass="$2"
    local url="${BASE_URL}/collection-panel/api/save-credentials"
    
    response=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"regtech_username\": \"$user\", \"regtech_password\": \"$pass\", \"secudium_username\": \"\", \"secudium_password\": \"\"}" \
        "$url")

    if echo "$response" | grep -q '"success": true'; then
        return 0
    else
        echo "API response did not indicate success. Response: $response"
        return 1
    fi
}

# Usage: test_load_credentials <expected_username>
test_load_credentials() {
    local expected_user="$1"
    local url="${BASE_URL}/collection-panel/api/load-credentials"
    
    response=$(curl -s -X GET "$url")

    if echo "$response" | grep -q "\"regtech_username\": \"$expected_user\""; then
        return 0
    else
        echo "Expected username not found in response. Response: $response"
        return 1
    fi
}

# Usage: test_health_check
test_health_check() {
    local url="${BASE_URL}/health"
    response=$(curl -s -X GET "$url")

    if echo "$response" | grep -q '"status": "healthy"'; then
        return 0
    else
        echo "Health check failed. Response: $response"
        return 1
    fi
}

# --- Main Script ---

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --user)
            REGTECH_USER="$2"
            shift
            shift
            ;; 
        --password)
            REGTECH_PASS="$2"
            shift
            shift
            ;; 
        *)
            echo "Unknown parameter passed: $1"
            exit 1
            ;; 
    esac
done

if [ -z "$REGTECH_USER" ] || [ -z "$REGTECH_PASS" ]; then
    echo "Usage: $0 --user <username> --password <password>"
    exit 1
fi


echo "=================================================="
echo "  Blacklist - Production Integration Test (Shell)"
echo "=================================================="

failed_tests=0
total_tests=0

# --- Step 1: Configuration ---
print_step "Step 1: Setting Credentials"
total_tests=$((total_tests+1))
run_test "Set REGTECH credentials via API" "test_set_credentials '$REGTECH_USER' '$REGTECH_PASS'" || failed_tests=$((failed_tests+1))
sleep 1

# --- Step 2: Verification ---
print_step "Step 2: Verifying System State"
total_tests=$((total_tests+1))
run_test "Check /health endpoint" "test_health_check" || failed_tests=$((failed_tests+1))

total_tests=$((total_tests+1))
run_test "Verify saved credentials" "test_load_credentials '$REGTECH_USER'" || failed_tests=$((failed_tests+1))


# --- Summary ---
echo -e "\n=================================================="
echo "                  Test Summary"
echo "=================================================="

passed_tests=$((total_tests - failed_tests))

if [ $failed_tests -eq 0 ]; then
    print_success "All $total_tests tests passed!"
else
    print_fail "$passed_tests/$total_tests tests passed."
fi

echo "--------------------------------------------------"
