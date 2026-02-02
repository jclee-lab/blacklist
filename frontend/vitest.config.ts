/**
 * Vitest Configuration for Frontend Unit Tests
 *
 * TEST DISCOVERY PATTERN:
 * - Uses physical directory: frontend/__tests__/
 * - Pattern: __tests__/**\/*.{test,spec}.{js,ts,jsx,tsx}
 *
 * MIGRATION NOTE (2026-02-02):
 * The test structure was migrated from centralized /tests/unit/ (symlink-based)
 * to frontend/__tests__/ (physical directories) to better support CI/CD pipelines
 * and Cloudflare Workers deployment. This was initiated in commit aec04a2.
 *
 * Test files are now co-located with the frontend code they test.
 *
 * STRUCTURE:
 * frontend/
 * ├── __tests__/              # Unit tests (Vitest)
 * │   └── components/
 * │       └── NavBar.test.tsx
 * ├── e2e/                    # E2E tests (Playwright)
 * │   ├── homepage.spec.ts
 * │   ├── ip-management.spec.ts
 * │   └── ...
 * ├── vitest.config.ts        # This file (Vitest config)
 * ├── playwright.config.ts    # Playwright config
 * └── vitest.setup.ts         # Vitest setup (JSX/DOM)
 *
 * RUNNING TESTS:
 * npm run test                      # Run all unit tests
 * npm run test:coverage             # With coverage report
 * npm run test:e2e                  # Run all E2E tests
 * npm run test:e2e -- --ui          # Interactive UI mode
 * npm run test:all                  # Both unit and E2E
 *
 * @see https://vitest.dev/config/
 * @see ./playwright.config.ts (E2E tests)
 * @see ../../.sisyphus/guides/test-commands-quick-reference.md
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Use jsdom for DOM/Browser APIs
    environment: 'jsdom',

    // Global test APIs (describe, it, expect) - no imports needed
    globals: true,

    // Setup file runs before all tests
    setupFiles: ['./vitest.setup.ts'],

    // TEST DISCOVERY: Matches the __tests__ directory
    // Finds all files matching: __tests__/**/*.test.tsx, __tests__/**/*.spec.ts, etc.
    include: ['__tests__/**/*.{test,spec}.{js,ts,jsx,tsx}'],

    // Exclude from test discovery
    exclude: ['node_modules/', 'e2e/', '**/*.config.{js,ts}', '**/dist/', '**/.next/'],

    // Code coverage settings
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'e2e/', '**/*.config.{js,ts}', '**/dist/', '**/.next/'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
