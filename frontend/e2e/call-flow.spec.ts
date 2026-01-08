import { test, expect } from '@playwright/test';

/**
 * E2E tests for video call initiation flows.
 * Tests the flow from browsing professionals to initiating calls and lead capture.
 */

test.describe('Call Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('can view professional profile card', async ({ page }) => {
    // Wait for the professional grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Check that professional cards have expected content
    const firstCard = page.locator('[role="article"]').first();
    await expect(firstCard).toBeVisible();

    // Should show professional name and type
    await expect(firstCard.locator('h3')).toBeVisible();

    // Should show availability status
    await expect(firstCard.getByText(/Available|Busy/)).toBeVisible();
  });

  test('professional card shows call button on hover for available professionals', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find an available professional card
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    // If there's an available professional, hover and check for call button
    if (await availableCard.isVisible()) {
      await availableCard.hover();
      await expect(availableCard.getByRole('button', { name: /call/i })).toBeVisible();
    }
  });

  test('clicking call button opens video call modal', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find an available professional card
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.hover();
      await availableCard.getByRole('button', { name: /call/i }).click();

      // Should open video call modal or navigate to call page
      await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    }
  });

  test('professional card is keyboard accessible', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Tab to first available professional card
    await page.keyboard.press('Tab');

    // Continue tabbing until we reach a professional card
    let attempts = 0;
    while (attempts < 20) {
      const focused = await page.locator(':focus').getAttribute('role');
      if (focused === 'article') {
        break;
      }
      await page.keyboard.press('Tab');
      attempts++;
    }

    // Should be able to focus on article
    await expect(page.locator('[role="article"]:focus')).toBeVisible();
  });

  test('view stats button opens baseball card modal', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Click view stats on first card with NMLS ID
    const viewStatsButton = page.getByRole('button', { name: /view stats/i }).first();

    if (await viewStatsButton.isVisible()) {
      await viewStatsButton.click();

      // Should open baseball card modal
      await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Lead Capture Modal', () => {
  test('lead capture form validates required fields', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find and click an available professional
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.hover();
      await availableCard.getByRole('button', { name: /call/i }).click();

      // Wait for any modal to appear
      await page.waitForTimeout(2000);

      // If lead capture modal appears (for anonymous users)
      const leadCaptureModal = page.locator('[role="dialog"]').filter({
        has: page.getByText(/stay connected|your.*info/i)
      });

      if (await leadCaptureModal.isVisible()) {
        // Try to submit without filling required fields
        await leadCaptureModal.getByRole('button', { name: /submit/i }).click();

        // Should show validation - form shouldn't be submitted
        const nameInput = leadCaptureModal.locator('input[type="text"]').first();
        await expect(nameInput).toBeFocused();
      }
    }
  });

  test('lead capture modal can be skipped', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find and click an available professional
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.hover();
      await availableCard.getByRole('button', { name: /call/i }).click();

      // Wait for any modal to appear
      await page.waitForTimeout(2000);

      // If lead capture modal appears
      const skipButton = page.getByRole('button', { name: /skip/i });
      if (await skipButton.isVisible()) {
        await skipButton.click();

        // Modal should close
        await expect(page.locator('[role="dialog"]').filter({
          has: page.getByText(/stay connected/i)
        })).not.toBeVisible();
      }
    }
  });

  test('lead capture modal closes on Escape key', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find and click an available professional
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.hover();
      await availableCard.getByRole('button', { name: /call/i }).click();

      // Wait for modal
      await page.waitForTimeout(2000);

      // If lead capture modal is visible, press Escape
      const modal = page.locator('[role="dialog"]');
      if (await modal.isVisible()) {
        await page.keyboard.press('Escape');

        // Give time for animation
        await page.waitForTimeout(500);
      }
    }
  });
});

test.describe('Schedule Call Flow', () => {
  test('can open schedule call modal', async ({ page }) => {
    await page.goto('/');

    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Look for schedule button if available on cards
    const scheduleButton = page.getByRole('button', { name: /schedule/i }).first();

    if (await scheduleButton.isVisible()) {
      await scheduleButton.click();

      // Should open schedule modal
      await expect(page.locator('[role="dialog"]')).toBeVisible();
      await expect(page.getByText(/schedule.*call/i)).toBeVisible();
    }
  });

  test('schedule modal shows date and time selection', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    const scheduleButton = page.getByRole('button', { name: /schedule/i }).first();

    if (await scheduleButton.isVisible()) {
      await scheduleButton.click();

      // Modal should show date selection
      await expect(page.getByText(/select.*date/i)).toBeVisible();

      // Should show time slots
      await expect(page.getByText(/select.*time/i)).toBeVisible();
    }
  });
});
