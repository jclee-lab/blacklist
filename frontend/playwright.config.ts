/**
 * Playwright E2E Testing Configuration
 *
 * TEST DISCOVERY PATTERN:
 * - testDir: './e2e' (symlink)
 * - Symlink target: frontend/e2e → ../tests/e2e
 * - Real test files location: /tests/e2e/**\/*.spec.ts
 * - File pattern: Files with .spec.ts extension
 *
 * SYMLINK STRUCTURE:
 * └─ Why symlinks? To keep tests centralized in /tests/ while maintaining
 *    clean separation from source code in frontend/
 *
 * IMPORTANT: If you move tests from /tests/ to frontend/e2e/:
 * 1. DELETE the symlink: rm frontend/e2e
 * 2. CREATE real directory: mkdir -p frontend/e2e
 * 3. COPY test files: cp -r tests/e2e/* frontend/e2e/
 * 4. UPDATE all imports: Change ../../ to ../ (may not be needed for E2E)
 * 5. NO CONFIG CHANGE NEEDED: testDir: './e2e' works with physical dirs too
 *
 * ENVIRONMENT VARIABLES:
 * - WEBKIT_ENABLED=true: Enable webkit/Safari tests (disabled by default)
 * - BASE_URL: Override test target URL (default: http://localhost:2543)
 * - CI: Enable CI-specific settings (retries, single worker)
 *
 * @see https://playwright.dev/docs/test-configuration
 * @see ../../.sisyphus/guides/frontend-test-structure.md (migration guide)
 */

import { defineConfig, devices } from '@playwright/test';

const webkitEnabled = process.env.WEBKIT_ENABLED === 'true';

export default defineConfig({
  // TEST DISCOVERY: Points to e2e symlink
  // Symlink target: /tests/e2e/
  testDir: './e2e',

  /* Global test timeout (default 30s is often too short for networkidle) */
  timeout: 60 * 1000,

  /* Assertion timeout */
  expect: {
    timeout: 10 * 1000,
  },

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'],
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.BASE_URL || 'http://localhost:2543',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',

    /* Navigation timeout */
    navigationTimeout: 30 * 1000,

    /* Action timeout */
    actionTimeout: 15 * 1000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    // Webkit requires specific system dependencies (libxml2, etc.)
    // Skip by default; enable with WEBKIT_ENABLED=true
    ...(webkitEnabled
      ? [
          {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
          },
        ]
      : []),

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },

    // Mobile Safari uses webkit engine - same dependency issue
    ...(webkitEnabled
      ? [
          {
            name: 'Mobile Safari',
            use: { ...devices['iPhone 12'] },
          },
        ]
      : []),
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:2543',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
