import { test, expect } from '@playwright/test';

test.describe('Collection Page - Basic Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');
  });

  test('should display collection page with header', async ({ page }) => {
    await expect(page.locator('h1').filter({ hasText: '데이터 수집' })).toBeVisible();
    await expect(page.getByText('REGTECH 데이터 수집 관리 및 이력')).toBeVisible();
  });

  test('should display all 4 tabs', async ({ page }) => {
    await expect(page.getByRole('tab', { name: '수집 관리' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '수집 데이터' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '인증정보' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '수집 이력' })).toBeVisible();
  });

  test('should default to management tab selected', async ({ page }) => {
    const managementTab = page.getByRole('tab', { name: '수집 관리' });
    await expect(managementTab).toHaveAttribute('aria-selected', 'true');
  });
});

test.describe('Collection Page - Tab Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');
  });

  test('should switch to data tab when clicked', async ({ page }) => {
    const dataTab = page.getByRole('tab', { name: '수집 데이터' });
    await dataTab.click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });

  test('should switch to credentials tab when clicked', async ({ page }) => {
    const credentialsTab = page.getByRole('tab', { name: '인증정보' });
    await credentialsTab.click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });

  test('should switch to history tab when clicked', async ({ page }) => {
    const historyTab = page.getByRole('tab', { name: '수집 이력' });
    await historyTab.click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });
});

test.describe('Collection Management Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');
  });

  test('should display collection status', async ({ page }) => {
    await expect(page.getByText('수집 상태')).toBeVisible();
  });

  test('should display total collected IPs', async ({ page }) => {
    await expect(page.getByText('총 수집 IP')).toBeVisible();
  });

  test('should display active collector count', async ({ page }) => {
    await expect(page.getByText('활성 수집기')).toBeVisible();
  });
});

test.describe('Collection History Tab', () => {
  test('should display history tab content', async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');

    await page.getByRole('tab', { name: '수집 이력' }).click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });
});

test.describe('Credentials Tab', () => {
  test('should display credentials tab content', async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');

    await page.getByRole('tab', { name: '인증정보' }).click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });
});

test.describe('Collected Data Tab', () => {
  test('should display data tab content', async ({ page }) => {
    await page.goto('/collection');
    await page.waitForLoadState('networkidle');

    await page.getByRole('tab', { name: '수집 데이터' }).click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });
});

test.describe('Collection Page - Responsive', () => {
  test('should be accessible on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only test');

    await page.goto('/collection');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h1').filter({ hasText: '데이터 수집' })).toBeVisible();
  });
});
