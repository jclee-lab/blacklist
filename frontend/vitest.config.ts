/**
 * Vitest Configuration for Frontend Unit Tests
 *
 * TEST DISCOVERY PATTERN:
 * - Uses symlink: frontend/__tests__ → ../tests/unit
 * - Real test files location: /tests/unit/**
 * - Pattern: __tests__/**\/*.{test,spec}.{js,ts,jsx,tsx}
 *
 * SYMLINK STRUCTURE:
 * └─ Why symlinks? To keep tests centralized in /tests/ while maintaining
 *    clean separation from source code in frontend/
 *
 * IMPORTANT: If you move tests from /tests/ to frontend/__tests__/:
 * 1. DELETE the symlink: rm frontend/__tests__
 * 2. CREATE real directory: mkdir -p frontend/__tests__
 * 3. COPY test files: cp -r tests/unit/* frontend/__tests__/
 * 4. UPDATE all imports: Change ../../components to ../components
 * 5. NO CONFIG CHANGE NEEDED: This pattern works with physical dirs too
 *
 * @see https://vitest.dev/config/
 * @see ../../.sisyphus/guides/frontend-test-structure.md (migration guide)
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

    // TEST DISCOVERY: Matches the __tests__ symlink
    // Points to: /tests/unit/**/*.test.tsx and similar
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
