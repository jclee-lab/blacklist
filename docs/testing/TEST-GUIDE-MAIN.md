# Blacklist Platform - Complete Testing Guide (Main Branch)

## Quick Reference

| Test Type | Framework | Count | When to Run | Time |
|-----------|-----------|-------|------------|------|
| Unit Tests | Vitest | 10+ | Every commit | 1-2m |
| Integration | Vitest | 20+ | PRs & CI | 2-3m |
| E2E Tests | Playwright | 50+ | Before merge | 5-10m |
| Visual Tests | Playwright | 40+ | UI changes | 3-5m |
| API Tests | Bash/curl | 15 | Every commit | 1m |
| **Total** | **Multiple** | **115+** | **Full suite** | **15-25m** |

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Test Overview](#test-overview)
4. [Running Tests](#running-tests)
5. [Understanding Results](#understanding-results)
6. [Common Failures & Fixes](#common-failures--fixes)
7. [Development Workflow](#development-workflow)
8. [CI/CD Integration](#cicd-integration)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## Quick Start

### For First-Time Setup

```bash
# 1. Navigate to project
cd /home/jclee/dev/blacklist

# 2. Install dependencies (if needed)
npm install

# 3. Run quick smoke tests
npm run test:unit

# 4. Run full E2E suite (longer)
npm run test:e2e

# 5. Check test coverage
npm run test:coverage
```

### For Daily Development

```bash
# Run tests relevant to your changes
npm run test:unit          # If you changed component logic
npm run test:e2e:homepage  # If you changed homepage
npm run test:api           # If you changed API integration
```

### Quick Sanity Check (30 seconds)

```bash
npm run test:unit --run    # Vitest single run mode
```

---

## Prerequisites & Setup

### System Requirements

- **Node.js**: v18+ (check with `node -v`)
- **npm**: v9+ (check with `npm -v`)
- **Browser**: Chrome/Chromium installed (for Playwright)
- **Disk Space**: ~2GB free (for node_modules + Playwright browsers)
- **OS**: Linux, macOS, or Windows (with WSL2)

### Installation

```bash
# 1. Install project dependencies
npm install

# 2. Install Playwright browsers (if not already done)
npx playwright install

# 3. Install Vitest (included in package.json)
npm install --save-dev vitest

# 4. Verify setup
npm run test:unit -- --version
npx playwright --version
```

### First-Time Configuration

```bash
# 1. Ensure .env.test exists (if needed)
# cp .env.example .env.test

# 2. Start dev server (for E2E tests)
npm run dev &

# 3. Wait for server to be ready
sleep 5

# 4. Run a single test to verify setup
npm run test:unit -- __tests__/simple.test.ts
```

---

## Test Overview

### Unit Tests (Vitest)

**What They Test**: Individual functions, components, utilities

**Examples**:
- Component rendering
- Function logic
- Utility calculations
- Data transformations

**Count**: 10+ tests
**Time**: 1-2 minutes
**When to Run**: Every commit

**File Locations**:
```
src/
├── components/
│   ├── Button.tsx
│   ├── Button.test.tsx          ← Unit test
│   ├── NavBar.tsx
│   └── NavBar.test.tsx          ← Unit test
├── utils/
│   ├── helpers.ts
│   └── helpers.test.ts          ← Unit test
└── hooks/
    ├── useFetch.ts
    └── useFetch.test.ts         ← Unit test
```

**Run Unit Tests**:
```bash
npm run test:unit                    # All unit tests
npm run test:unit -- Button          # Specific component
npm run test:unit -- --coverage      # With coverage report
npm run test:unit -- --watch         # Watch mode (re-run on change)
```

### Integration Tests (Vitest)

**What They Test**: Multiple components working together, component interactions

**Examples**:
- NavBar + MenuDropdown interaction
- Form submission flow
- Navigation between pages
- Data loading + display

**Count**: 20+ tests
**Time**: 2-3 minutes
**When to Run**: Before PRs, in CI/CD

**File Locations**:
```
tests/
├── integration/
│   ├── navbar-menu.test.tsx
│   ├── form-validation.test.tsx
│   ├── auth-flow.test.tsx
│   └── page-navigation.test.tsx
```

**Run Integration Tests**:
```bash
npm run test:integration              # All integration tests
npm run test:integration -- auth      # Tests matching "auth"
npm run test:integration -- --ui      # Vitest UI mode
```

### E2E Tests (Playwright)

**What They Test**: Complete user workflows from start to finish

**Examples**:
- User visits homepage
- User navigates to product page
- User fills form and submits
- User logs in and accesses dashboard
- Complete checkout flow

**Count**: 50+ tests
**Time**: 5-10 minutes (depending on concurrency)
**When to Run**: Before merge, full CI/CD

**File Locations**:
```
tests/
├── e2e/
│   ├── homepage.spec.ts
│   ├── navigation.spec.ts
│   ├── authentication.spec.ts
│   ├── forms.spec.ts
│   ├── checkout.spec.ts
│   └── dashboard.spec.ts
```

**Run E2E Tests**:
```bash
npm run test:e2e                      # All E2E tests
npm run test:e2e -- --headed          # See browser window
npm run test:e2e -- --debug           # Debug mode
npm run test:e2e -- --workers=1       # Serial execution
npm run test:e2e -- homepage          # Specific test file
```

### Visual Tests (Playwright)

**What They Test**: Visual appearance consistency across browsers

**Examples**:
- Button styling is correct
- Layout is responsive
- Colors match design
- Typography is correct
- Spacing is consistent

**Count**: 40+ tests
**Time**: 3-5 minutes
**When to Run**: After UI changes, design updates

**File Locations**:
```
tests/
└── visual/
    ├── buttons.visual.spec.ts
    ├── forms.visual.spec.ts
    ├── layouts.visual.spec.ts
    └── responsive.visual.spec.ts
```

**Run Visual Tests**:
```bash
npm run test:visual                   # All visual tests
npm run test:visual -- --update       # Update baseline screenshots
npm run test:visual -- --headed       # See comparison
```

### API Tests (Bash/curl)

**What They Test**: Backend API endpoints, status codes, response formats

**Examples**:
- GET /api/users returns 200
- POST /api/users creates user
- Invalid data returns 400
- Authentication required returns 401
- CORS headers present

**Count**: 15 tests
**Time**: 1 minute
**When to Run**: Every commit, especially backend changes

**File Locations**:
```
tests/
└── api/
    ├── users.api.test.sh
    ├── products.api.test.sh
    ├── auth.api.test.sh
    └── health.api.test.sh
```

**Run API Tests**:
```bash
npm run test:api                      # All API tests
npm run test:api:users                # Specific endpoint tests
bash tests/api/users.api.test.sh      # Run directly
```

---

## Running Tests

### Individual Test Suites

#### Unit Tests

```bash
# Run all unit tests
npm run test:unit

# Run with coverage report
npm run test:unit -- --coverage

# Run in watch mode (re-runs on file change)
npm run test:unit -- --watch

# Run specific test file
npm run test:unit -- Button.test.tsx

# Run tests matching pattern
npm run test:unit -- --grep "renders"

# Run with UI dashboard
npm run test:unit -- --ui
```

#### Integration Tests

```bash
# Run all integration tests
npm run test:integration

# Run specific suite
npm run test:integration -- navbar

# Run with detailed output
npm run test:integration -- --reporter=verbose

# Run and update snapshots
npm run test:integration -- --update
```

#### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run specific file
npm run test:e2e -- homepage.spec.ts

# Run with visible browser window
npm run test:e2e -- --headed

# Run in headed mode with slow motion
npm run test:e2e -- --headed --headed-slow-motion=1000

# Run single test from file
npm run test:e2e -- --grep "User can navigate"

# Debug mode (opens inspector)
npm run test:e2e -- --debug

# Run in serial (one test at a time)
npm run test:e2e -- --workers=1

# Run with specific browser
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit
```

#### Visual Tests

```bash
# Run all visual tests
npm run test:visual

# Update baseline screenshots (after design changes)
npm run test:visual -- --update

# Run specific test
npm run test:visual -- buttons.visual.spec.ts

# Run with headed mode to see comparisons
npm run test:visual -- --headed

# Run and generate report
npm run test:visual -- --reporter=html
```

#### API Tests

```bash
# Run all API tests
npm run test:api

# Run specific endpoint tests
npm run test:api:users
npm run test:api:products
npm run test:api:auth

# Run with detailed output
bash tests/api/users.api.test.sh -v

# Run against different environment
API_BASE_URL=https://staging.example.com npm run test:api
```

### Combined Test Runs

```bash
# Run all tests (unit, integration, E2E, visual, API)
npm run test:all

# Run all except E2E (faster feedback)
npm run test:fast

# Run tests for specific feature area
npm run test:unit -- auth
npm run test:e2e -- --grep "auth"
npm run test:api:auth

# Run before committing
npm run test:pre-commit

# Run before pushing
npm run test:pre-push
```

---

## Understanding Results

### Vitest Output

```
✓ src/components/Button.test.tsx (3)
  ✓ Button renders correctly (24ms)
  ✓ Button handles click (18ms)
  ✓ Button shows loading state (15ms)

✓ src/utils/helpers.test.ts (2)
  ✓ formatDate works (5ms)
  ✓ calculateTotal works (4ms)

Test Files  2 passed (2)
     Tests  5 passed (5)
  Duration  2.34s
```

**Interpretation**:
- ✓ = Test passed
- ✗ = Test failed
- Indented items = Individual test cases
- Numbers in parentheses = Time taken in milliseconds
- Final line = Total time for all tests

### Coverage Report

```
File                  % Stmts % Branch % Funcs % Lines
─────────────────────────────────────────────────────
All files               85.2    78.4    82.1    84.9
 src/components/       90.1    85.2    88.3    89.5
  Button.tsx           95.0    90.0    95.0    95.0
  NavBar.tsx           88.0    82.0    85.0    87.0
 src/utils/            82.3    72.1    81.0    81.5
  helpers.ts           82.3    72.1    81.0    81.5
```

**Interpretation**:
- % Stmts = Percentage of code statements executed
- % Branch = Percentage of conditional branches tested
- % Funcs = Percentage of functions called
- % Lines = Percentage of lines covered

**Good Coverage**: 80%+ is generally considered good
**Excellent Coverage**: 90%+ indicates thorough testing
**Low Coverage**: Below 60% suggests missing test cases

### Playwright E2E Output

```
Running 50 tests using 4 workers

  ✓ [chromium] homepage.spec.ts (3)
    ✓ Page loads successfully (1.2s)
    ✓ Navigation links work (0.8s)
    ✓ Search functionality works (1.5s)

  ✓ [firefox] homepage.spec.ts (3)
  
  ✓ [webkit] homepage.spec.ts (3)

  ✓ navigation.spec.ts (5)
  ✓ authentication.spec.ts (8)
  
  ✗ [chromium] forms.spec.ts (1)
    ✗ Form validation shows errors (timeout: 5000ms)

Summary:
  49 passed, 1 failed
  Duration: 3m 42s
```

**Interpretation**:
- ✓ = Test passed
- ✗ = Test failed with reason
- Numbers in brackets = Browser (chromium, firefox, webkit)
- Time shown = Duration for that test
- Summary = Overall results

### Visual Test Output

```
Visual test results:
  ✓ buttons.visual.spec.ts
    ✓ Primary button looks correct
    ✓ Secondary button looks correct
    ✓ Button in dark mode looks correct

  ✓ forms.visual.spec.ts
  
  ✗ responsive.visual.spec.ts
    ✗ Layout on mobile looks different (3 pixels diff detected)

Baselines: 43 passed, 1 new, 0 changed
HTML Report: test-results/index.html
```

---

## Common Failures & Fixes

### 1. "Timeout: 5000ms exceeded"

**Cause**: Element didn't appear in time, page didn't load

**Fix**:
```javascript
// Increase timeout for specific test
test('slow feature', async ({ page }) => {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.locator('button').click({ timeout: 10000 });
});

// Or globally in playwright.config.ts
timeout: 30000, // 30 seconds per test
navigationTimeout: 30000,
```

### 2. "Expected localhost:3000 to be running"

**Cause**: Dev server not running

**Fix**:
```bash
# Start dev server in background
npm run dev &

# Wait for server to be ready
sleep 3

# Then run tests
npm run test:e2e
```

### 3. "Module not found: 'vitest'"

**Cause**: Dependencies not installed

**Fix**:
```bash
# Clean reinstall
rm -rf node_modules package-lock.json
npm install

# Or just update
npm install --save-dev vitest
```

### 4. "Playwright browser not found"

**Cause**: Browsers not installed

**Fix**:
```bash
# Install Playwright browsers
npx playwright install

# Or specific browser
npx playwright install chromium
```

### 5. "EADDRINUSE: address already in use :::3000"

**Cause**: Port 3000 already in use (from previous dev server)

**Fix**:
```bash
# Kill process using port 3000
kill $(lsof -t -i:3000)

# Or use different port
PORT=3001 npm run dev
```

### 6. "AssertionError: expected [] to have length 5"

**Cause**: Selector found wrong number of elements

**Fix**:
```javascript
// Debug: inspect page
await page.screenshot({ path: 'debug.png' });
console.log(await page.locator('button').all());

// Fix: more specific selector
await page.locator('form button').click(); // more specific
```

### 7. "Test file not found"

**Cause**: Test file path incorrect

**Fix**:
```bash
# Find correct path
find . -name "*.test.ts" | grep -i button

# Run with correct path
npm run test:unit -- src/components/Button.test.tsx
```

### 8. "Visual baseline not found"

**Cause**: First run of visual test, no baseline to compare

**Fix**:
```bash
# Generate initial baseline
npm run test:visual -- --update

# This creates baseline screenshots
# Future runs will compare against them
```

---

## Development Workflow

### Typical Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-button

# 2. Write component code
# Edit: src/components/NewButton.tsx

# 3. Write unit tests
# Edit: src/components/NewButton.test.tsx

# 4. Run tests while developing
npm run test:unit -- NewButton --watch

# 5. When component complete, add integration test
# Edit: tests/integration/page-with-button.test.tsx

# 6. Run integration tests
npm run test:integration

# 7. Add E2E test for user workflow
# Edit: tests/e2e/user-flow.spec.ts

# 8. Run E2E tests
npm run test:e2e -- user-flow

# 9. Add visual test if styling changed
# Edit: tests/visual/buttons.visual.spec.ts
npm run test:visual -- --update

# 10. Run all tests before committing
npm run test:all

# 11. Commit changes
git add .
git commit -m "feat: add new button component with tests"

# 12. Push and create PR
git push origin feature/new-button
```

### Test-Driven Development (TDD)

```bash
# 1. Write test first (will fail)
# Edit: src/components/Counter.test.tsx
npm run test:unit -- Counter

# ✗ Counter increments on click (FAILS)

# 2. Implement component to make test pass
# Edit: src/components/Counter.tsx

# 3. Run test again
npm run test:unit -- Counter

# ✓ Counter increments on click (PASSES)

# 4. Write more test cases
# Add: "decrement", "reset" tests

# 5. Implement features for those tests

# 6. Continue until feature complete
```

### Debugging Tests

```javascript
// 1. Add console logs
test('user interaction', async ({ page }) => {
  console.log('Starting test');
  await page.goto('/');
  console.log('Page loaded');
  
  const button = page.locator('button');
  console.log('Button found');
  await button.click();
  console.log('Button clicked');
});

// 2. Use debug mode
test.only('debug this test', async ({ page }) => {
  // This test runs alone, with inspector open
  // npm run test:e2e -- --debug
  await page.pause(); // Pauses during execution
});

// 3. Take screenshots at key points
await page.screenshot({ path: 'step1.png' });
await page.click('button');
await page.screenshot({ path: 'step2.png' });

// 4. Use headed mode to see what's happening
// npm run test:e2e -- --headed

// 5. Print page content for debugging
console.log(await page.content());
console.log(await page.locator('body').innerHTML());
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:unit
      
      - name: Run integration tests
        run: npm run test:integration
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Run API tests
        run: npm run test:api
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/

  visual:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Use Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 20.x
          cache: 'npm'
      
      - name: Install and run visual tests
        run: |
          npm ci
          npm run test:visual
      
      - name: Upload visual report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: visual-report
          path: test-results/
```

### Pre-commit Hook

```bash
#!/bin/bash
# .husky/pre-commit

npm run test:unit
npm run test:api

if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```

---

## Performance Optimization

### Run Tests Faster

```bash
# 1. Run only unit tests (fastest feedback)
npm run test:unit

# 2. Skip slow visual tests during development
npm run test:unit && npm run test:integration

# 3. Run tests in parallel (default for E2E)
npm run test:e2e -- --workers=4

# 4. Run only affected tests (requires git)
npm run test:unit -- --changed
npm run test:integration -- --changed

# 5. Run specific test file (faster than full suite)
npm run test:unit -- Button.test.tsx
```

### Optimize CI/CD

```yaml
# Matrix strategy runs tests in parallel
strategy:
  matrix:
    test-type: [unit, integration, e2e, api]
    
jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Run ${{ matrix.test-type }} tests
        run: npm run test:${{ matrix.test-type }}
```

### Local Performance Tips

```bash
# 1. Use watch mode for fast feedback
npm run test:unit -- --watch

# 2. Run only failing tests
npm run test:unit -- --fail-fast

# 3. Increase Node memory for large suites
NODE_OPTIONS=--max-old-space-size=4096 npm run test:all

# 4. Run tests with SSD (tmpfs) for speed
export TMPDIR=/dev/shm
npm run test:e2e
```

---

## Troubleshooting Guide

### Issue: Tests Pass Locally But Fail in CI

**Cause**: Environment difference (OS, node version, paths)

**Solution**:
```bash
# 1. Check Node version matches CI
node -v  # Compare with CI config

# 2. Clear cache and reinstall
npm ci  # Same as npm install but for CI

# 3. Run with same conditions as CI
npm run test:unit -- --run  # Non-watch mode

# 4. Check file paths are relative, not absolute
# ✓ Good: './tests/data.json'
# ✗ Bad: '/home/user/project/tests/data.json'
```

### Issue: Tests Hang or Freeze

**Cause**: Infinite loop, unresolved promise, or port conflict

**Solution**:
```bash
# 1. Add timeout to hung test
test.setTimeout(10000); // 10 second timeout

# 2. Check for open ports
lsof -i :3000

# 3. Kill stuck processes
killall node

# 4. Check for unresolved promises
test('async operation', async () => {
  const result = await fetch('/api/data');
  // Always await async operations
});
```

### Issue: Flaky Tests (Pass Sometimes, Fail Sometimes)

**Cause**: Timing issues, race conditions, port conflicts

**Solution**:
```javascript
// 1. Add explicit wait for elements
await page.waitForSelector('button');
await page.click('button');

// 2. Increase timeouts for slower environments
test('slow operation', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
}, { timeout: 30000 });

// 3. Clear state between tests
beforeEach(() => {
  // Reset database
  // Clear cache
  // Clear local storage
});

// 4. Avoid hardcoded waits
// ✗ Bad: await page.waitForTimeout(1000);
// ✓ Good: await page.waitForSelector('button');
```

### Issue: Out of Memory

**Cause**: Too many tests running in parallel, memory leak

**Solution**:
```bash
# 1. Reduce parallel workers
npm run test:e2e -- --workers=1

# 2. Increase Node memory
NODE_OPTIONS=--max-old-space-size=4096 npm run test:all

# 3. Run test suites separately
npm run test:unit
npm run test:integration
npm run test:e2e

# 4. Check for memory leaks in tests
# Look for: page.goto() without page.close()
```

### Issue: "Cannot find module" in tests

**Cause**: Import path wrong, file not found, alias not configured

**Solution**:
```javascript
// 1. Check file exists at path
// ✓ Good: import Button from '../components/Button'
// ✗ Bad: import Button from '../component/Button'

// 2. Use path aliases if configured
// tsconfig.json: "@components/*": ["src/components/*"]
// Then: import Button from '@components/Button'

// 3. Check vite.config.ts or vitest.config.ts
// Should have resolve.alias configured

// 4. Reload IDE/editor if just added
```

---

## Last Updated

**Date**: February 1, 2025
**Test Framework Versions**:
- Vitest: 1.0+
- Playwright: 1.40+
- Node.js: 18+

**See Also**:
- TEST-INFRASTRUCTURE-DISCOVERY.md - Complete test inventory
- TEST-GUIDE-AIRGAP.md - Airgap branch testing (15 Bash E2E tests)
- docs/REFERENCE-*.ts - Example test code files

**Next**: See TEST-EXECUTION-RESULTS.md for actual test run results and metrics
