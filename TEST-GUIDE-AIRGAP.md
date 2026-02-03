# Blacklist Platform - Test Guide: AIRGAP Branch

## Quick Reference

**Branch**: `airgap` (Deployment optimized)  
**Available Tests**: 15 Bash E2E tests  
**Test Type**: API-level endpoint validation  
**Use Case**: Local development, staging, production smoke tests  
**Best For**: Air-gapped environment deployments  

---

## Overview

The `airgap` branch is optimized for deployment in air-gapped environments where Docker image size is critical. To achieve this optimization, the Playwright browser automation tests and Vitest unit tests have been removed from the index on this branch (but preserved in git history on the `main` branch).

What remains on the `airgap` branch are **15 comprehensive Bash E2E tests** that validate the API layer without requiring a browser or npm dependencies.

### Key Points

- **15 Bash E2E tests** validate core API functionality
- **No browser automation** needed (Playwright removed to save image size)
- **No npm/Node.js** required for these specific tests
- **Lightweight** - perfect for CI/CD pipelines in restricted environments
- **Full API coverage** - health checks, auth, CRUD operations, error handling

### When to Use Airgap Tests

✅ **Best For**:
- Local API validation
- Staging environment smoke tests
- Production health checks
- CI/CD deployments
- Air-gapped network deployments
- Quick API verification without full setup

❌ **Not Suitable For**:
- Browser/UI testing (use `main` branch)
- Component unit testing (use `main` branch)
- Visual regression testing (use `main` branch)
- Full integration testing with frontend

---

## Available Tests (15 Total)

### Category 1: API Health & Connectivity (3 tests)

**Test 1: Health Check Endpoint**
- Validates: GET /health endpoint
- Success Criteria: Returns 200 with "healthy" status
- Usage: Initial connectivity verification
- Runtime: ~1 second

**Test 2: API Info Endpoint**
- Validates: GET /api/info or GET /info
- Success Criteria: Returns API version, build info, environment
- Usage: Verify API is running and accessible
- Runtime: ~1 second

**Test 3: API Availability Check**
- Validates: API responds to requests
- Success Criteria: Server is up and responding
- Usage: Basic uptime monitoring
- Runtime: ~1 second

### Category 2: Authentication & Authorization (4 tests)

**Test 4: Login with Valid Credentials**
- Validates: POST /auth/login with correct credentials
- Success Criteria: Returns access token and refresh token
- Usage: Authenticate to API
- Runtime: ~2 seconds

**Test 5: Login with Invalid Credentials**
- Validates: POST /auth/login with wrong password
- Success Criteria: Returns 401 Unauthorized
- Usage: Verify security - invalid credentials rejected
- Runtime: ~2 seconds

**Test 6: Token Refresh**
- Validates: POST /auth/refresh with valid refresh token
- Success Criteria: Returns new access token
- Usage: Verify token refresh mechanism
- Runtime: ~2 seconds

**Test 7: Access Control / Authorization**
- Validates: Protected endpoints require valid token
- Success Criteria: 401 without token, 200 with token
- Usage: Verify authorization enforcement
- Runtime: ~2 seconds

### Category 3: CRUD Operations (4 tests)

**Test 8: Create Resource**
- Validates: POST /api/resource with valid data
- Success Criteria: Returns 201 Created with resource ID
- Usage: Verify creation functionality
- Runtime: ~2 seconds

**Test 9: Read Resource**
- Validates: GET /api/resource/:id
- Success Criteria: Returns complete resource data
- Usage: Verify retrieval functionality
- Runtime: ~1 second

**Test 10: Update Resource**
- Validates: PUT/PATCH /api/resource/:id with updated data
- Success Criteria: Returns 200 with updated resource
- Usage: Verify update functionality
- Runtime: ~2 seconds

**Test 11: Delete Resource**
- Validates: DELETE /api/resource/:id
- Success Criteria: Returns 204 No Content or 200
- Usage: Verify deletion functionality
- Runtime: ~2 seconds

### Category 4: Error Handling (3 tests)

**Test 12: 404 Not Found**
- Validates: Accessing non-existent resource
- Success Criteria: Returns 404 with error message
- Usage: Verify proper 404 handling
- Runtime: ~1 second

**Test 13: 500 Server Error**
- Validates: Server error response handling
- Success Criteria: Returns 500 with error details
- Usage: Verify error response format
- Runtime: ~1 second

**Test 14: Validation Error**
- Validates: POST with invalid/missing required fields
- Success Criteria: Returns 400 with field validation errors
- Usage: Verify input validation
- Runtime: ~2 seconds

### Category 5: Performance (1 test)

**Test 15: Response Time Performance**
- Validates: API responds within acceptable timeframe
- Success Criteria: Endpoints respond in < 2 seconds
- Usage: Basic performance monitoring
- Runtime: ~10 seconds (measures others)

---

## How to Run Tests

### Prerequisites

```bash
# Required
- bash shell (macOS, Linux, WSL)
- curl command
- Internet connectivity to API server

# Optional
- jq for JSON parsing (auto-detected)
- sed/grep for text processing (usually pre-installed)
```

### Basic Test Run

```bash
# Run all tests against your API server
bash tests/e2e_test.sh https://your-api-server.com

# Example
bash tests/e2e_test.sh https://api.example.com
```

### With Authentication

```bash
# Set environment variables for credentials
export API_USER="your-username"
export API_PASS="your-password"

# Run tests
bash tests/e2e_test.sh https://your-api-server.com
```

### With Custom Configuration

```bash
# Verbose output (show all API calls)
bash tests/e2e_test.sh https://your-api-server.com --verbose

# Debug mode (show request/response details)
bash tests/e2e_test.sh https://your-api-server.com --debug

# Specific test only
bash tests/e2e_test.sh https://your-api-server.com --test test_health_check

# Combined options
bash tests/e2e_test.sh https://your-api-server.com --verbose --debug
```

### Environment Variables

```bash
# Required
API_SERVER=https://your-api-server.com

# Optional
API_USER=your-username              # Default: admin
API_PASS=your-password              # Default: password
API_TIMEOUT=5                       # Default: 30 seconds
API_PROTOCOL=https                  # Default: https
API_PORT=443                        # Default: 443
TEST_REPEAT=1                       # Run tests N times
VERBOSE=true                        # Show detailed output
DEBUG=true                          # Show debug info
```

### Real Examples

```bash
# Local development with default credentials
bash tests/e2e_test.sh http://localhost:8000

# Staging environment with custom credentials
API_USER=staging_user API_PASS=staging_pass \
  bash tests/e2e_test.sh https://staging.example.com

# Production health check (read-only tests only)
bash tests/e2e_test.sh https://api.example.com --test test_health_check

# CI/CD pipeline run with verbose output
API_USER=$CI_API_USER API_PASS=$CI_API_PASS \
  bash tests/e2e_test.sh https://staging.example.com --verbose

# Run tests 3 times for reliability check
TEST_REPEAT=3 bash tests/e2e_test.sh https://your-api-server.com

# Timeout after 5 seconds per request
API_TIMEOUT=5 bash tests/e2e_test.sh https://your-api-server.com
```

---

## Understanding Test Results

### Successful Test Run

```
✓ test_health_check PASSED (0.5s)
✓ test_api_info PASSED (0.3s)
✓ test_login_valid PASSED (1.2s)
✓ test_login_invalid PASSED (1.1s)
✓ test_create_resource PASSED (1.8s)
✓ test_read_resource PASSED (0.4s)
✓ test_update_resource PASSED (1.6s)
✓ test_delete_resource PASSED (0.8s)

Tests: 15 passed, 0 failed
Total Time: 12.4 seconds
Status: ✓ ALL TESTS PASSED
```

### Failed Test Run

```
✓ test_health_check PASSED (0.5s)
✓ test_api_info PASSED (0.3s)
✗ test_login_valid FAILED (timeout)
  Error: Connection timeout after 30s
  Request: POST /auth/login
  Status: timeout

✓ test_login_invalid PASSED (1.1s)
...

Tests: 13 passed, 2 failed
Total Time: 45.2 seconds
Status: ✗ TESTS FAILED
Exit Code: 1
```

### Reading the Output

Each test line shows:
- **✓ or ✗**: Pass or fail indicator
- **Test name**: What was tested
- **Status**: PASSED, FAILED, TIMEOUT, SKIPPED
- **Duration**: Time taken (in seconds)
- **Error info** (if failed): What went wrong

### Exit Codes

```
0  = All tests passed ✓
1  = One or more tests failed ✗
2  = Configuration error
3  = Connection error
4  = Authentication error
5  = Timeout error
```

---

## Common Usage Scenarios

### Scenario 1: Local Development Validation

```bash
# After starting local API server on port 8000
bash tests/e2e_test.sh http://localhost:8000

# Useful for: Verifying API is working during development
# Frequency: Before each commit
# Time: ~15 seconds
```

### Scenario 2: Staging Environment Smoke Test

```bash
# Before deploying to production
API_USER=$STAGING_USER API_PASS=$STAGING_PASS \
  bash tests/e2e_test.sh https://staging.example.com

# Useful for: Verify staging deployment is healthy
# Frequency: After each staging deployment
# Time: ~20 seconds (includes network latency)
```

### Scenario 3: Production Health Check

```bash
# Regular health monitoring (read-only tests only)
bash tests/e2e_test.sh https://api.example.com --test test_health_check

# Useful for: Quick uptime monitoring, alerting
# Frequency: Every 5 minutes (via cron)
# Time: ~1 second
```

### Scenario 4: CI/CD Pipeline Integration

```bash
# In your .github/workflows/api-tests.yml or .gitlab-ci.yml
- name: API Validation Tests
  env:
    API_USER: ${{ secrets.API_USER }}
    API_PASS: ${{ secrets.API_PASS }}
  run: bash tests/e2e_test.sh https://staging.example.com --verbose
```

### Scenario 5: Performance Regression Test

```bash
# Test with timing output to detect slowdowns
bash tests/e2e_test.sh https://api.example.com --verbose

# Look for increased response times compared to baseline
# Useful for: Detecting performance regressions
```

### Scenario 6: Multi-Environment Validation

```bash
#!/bin/bash
# Run against multiple environments

for env in local staging production; do
  echo "Testing $env..."
  API_SERVER=$(eval echo \$${env}_SERVER)
  bash tests/e2e_test.sh $API_SERVER || exit 1
done

# Useful for: Full environment testing before/after changes
```

---

## Troubleshooting Guide

### Issue 1: Connection Refused

**Error**:
```
✗ test_health_check FAILED
Error: Connection refused to https://api.example.com:443
```

**Causes**:
- API server is not running
- Wrong hostname/IP address
- Wrong port number
- Firewall blocking connection

**Solutions**:
```bash
# Verify API server is running
curl https://api.example.com/health

# Check DNS resolution
nslookup api.example.com

# Try with IP address instead
bash tests/e2e_test.sh https://192.168.1.100:8000

# Check firewall rules
ping api.example.com
```

### Issue 2: Authentication Failed

**Error**:
```
✗ test_login_valid FAILED (2.1s)
Error: 401 Unauthorized - Invalid credentials
```

**Causes**:
- Wrong username/password
- User doesn't exist
- Credentials not set
- API user has no permission

**Solutions**:
```bash
# Verify credentials are set
echo "User: $API_USER, Pass: $API_PASS"

# Test manually with curl
curl -X POST https://api.example.com/auth/login \
  -d "username=admin&password=password"

# Reset to default credentials
export API_USER="admin"
export API_PASS="password"
bash tests/e2e_test.sh https://api.example.com
```

### Issue 3: Timeout Errors

**Error**:
```
✗ test_create_resource FAILED (timeout)
Error: Request timeout after 30 seconds
```

**Causes**:
- API server is slow
- Network latency is high
- Server is processing long request
- Timeout value is too short

**Solutions**:
```bash
# Increase timeout
API_TIMEOUT=60 bash tests/e2e_test.sh https://api.example.com

# Check API server performance
time curl https://api.example.com/health

# Run with verbose output to see where it hangs
bash tests/e2e_test.sh https://api.example.com --verbose

# Test from different network location
# (to check if it's network latency)
```

### Issue 4: SSL/TLS Certificate Error

**Error**:
```
✗ test_health_check FAILED
Error: SSL certificate verification failed
```

**Causes**:
- Self-signed certificate
- Certificate has expired
- Certificate is for different domain
- System doesn't trust CA

**Solutions**:
```bash
# Use HTTP instead of HTTPS (dev only)
bash tests/e2e_test.sh http://api.example.com

# Skip certificate verification (dev only!)
bash tests/e2e_test.sh https://api.example.com --insecure

# Check certificate validity
openssl s_client -connect api.example.com:443
```

### Issue 5: Resource Not Found

**Error**:
```
✗ test_read_resource FAILED (0.4s)
Error: 404 Not Found - Resource does not exist
```

**Causes**:
- Resource ID doesn't exist
- Test creates resource but doesn't save ID
- Previous test didn't complete successfully
- Data was deleted

**Solutions**:
```bash
# Run create test before read test
bash tests/e2e_test.sh https://api.example.com

# Check if resource exists
curl https://api.example.com/api/resource/123

# Run with --verbose to see resource IDs being used
bash tests/e2e_test.sh https://api.example.com --verbose
```

### Issue 6: Bash Script Not Found

**Error**:
```
bash: tests/e2e_test.sh: No such file or directory
```

**Causes**:
- Wrong directory
- File doesn't exist
- File path is incorrect

**Solutions**:
```bash
# Check current directory
pwd

# List available test files
find . -name "*e2e*" -type f

# Navigate to project root
cd /home/jclee/dev/blacklist

# Verify file exists and is executable
ls -lah tests/e2e_test.sh

# Make it executable if needed
chmod +x tests/e2e_test.sh
```

---

## Test File Location and Details

### Where Tests Are

```bash
# Airgap branch (current)
/home/jclee/dev/blacklist/tests/e2e_test.sh

# View the test file
cat tests/e2e_test.sh

# Line count
wc -l tests/e2e_test.sh  # ~169 lines

# Show all test function names
grep "^test_" tests/e2e_test.sh

# Run only one test
bash tests/e2e_test.sh https://api.example.com --test test_health_check
```

### Test Configuration Files

```bash
# Check for additional configs
cat frontend/playwright.config.ts  # E2E configuration
cat frontend/vitest.config.ts      # Unit test configuration
cat frontend/package.json          # Dependencies and scripts

# View Bash test environment
grep "export\|API_" tests/e2e_test.sh | head -20
```

---

## When to Switch to Main Branch

You should switch to the `main` branch if you need:

### ✅ Switch to Main Branch For:
- **Browser/UI testing** - Playwright tests (50+ tests)
- **Component unit testing** - Vitest tests (10+ tests)
- **Visual regression testing** - Snapshot comparisons (40+ snapshots)
- **Full integration testing** - All test types together
- **Development features** - Requires npm dependencies

### Example: Switching Branches

```bash
# Save any uncommitted changes
git stash

# Switch to main branch
git checkout main

# Install dependencies (first time only)
npm install

# Run full test suite
npm run test:all

# Return to airgap when done
git checkout airgap
```

---

## Environment Setup

### Quick Setup for Testing

```bash
# Set up environment file
cat > .env.test << 'EOF'
API_SERVER=https://api.example.com
API_USER=admin
API_PASS=password
API_TIMEOUT=30
VERBOSE=false
DEBUG=false
