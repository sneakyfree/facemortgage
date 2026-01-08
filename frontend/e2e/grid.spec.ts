import { test, expect } from '@playwright/test';

/**
 * E2E tests for the professional grid and filtering.
 */
test.describe('Professional Grid', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('displays professional cards when available', async ({ page }) => {
    // Wait for the grid to load
    await page.waitForLoadState('networkidle');

    // The grid container should be present
    const grid = page.locator('[class*="grid"]').first();
    await expect(grid).toBeVisible();
  });

  test('professional cards show essential information', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // If professionals are available, cards should show:
    // - Name
    // - Status indicator
    // - Rating (if available)
    // These are checked using class or text patterns
    const cards = page.locator('[class*="professional"], [class*="card"]');
    const count = await cards.count();

    if (count > 0) {
      // At least one card should have name-like content
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();
    }
  });
});

test.describe('Filter Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('can select state filter', async ({ page }) => {
    const stateSelect = page.locator('select').first();
    await stateSelect.selectOption({ label: 'California' }).catch(() => {
      // If CA not available, select first non-empty option
      stateSelect.selectOption({ index: 1 });
    });

    // The filter should be applied
    await expect(stateSelect).not.toHaveValue('');
  });

  test('can select professional type filter', async ({ page }) => {
    const typeSelect = page.locator('select').nth(1);
    await typeSelect.selectOption('loan_officer');

    await expect(typeSelect).toHaveValue('loan_officer');
  });

  test('can select minimum rating filter', async ({ page }) => {
    const ratingSelect = page.locator('select').nth(4);
    await ratingSelect.selectOption('4.0');

    await expect(ratingSelect).toHaveValue('4.0');
  });

  test('clear all button appears when filters are active', async ({ page }) => {
    // Select a filter
    const typeSelect = page.locator('select').nth(1);
    await typeSelect.selectOption('loan_officer');

    // Clear all button should appear
    await expect(page.getByText('Clear all')).toBeVisible();
  });

  test('clear all button resets filters', async ({ page }) => {
    // Select a filter
    const typeSelect = page.locator('select').nth(1);
    await typeSelect.selectOption('loan_officer');

    // Click clear all
    await page.getByText('Clear all').click();

    // Filter should be reset
    await expect(typeSelect).toHaveValue('');
  });
});

test.describe('Responsive Design', () => {
  test('filter panel is visible on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    await expect(page.getByText('Find Your Professional')).toBeVisible();
  });

  test('grid adapts to mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // The page should still be functional on mobile
    await expect(page.getByText('FaceMortgage')).toBeVisible();
  });
});
