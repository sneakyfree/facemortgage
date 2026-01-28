import { test, expect } from '@playwright/test';

/**
 * E2E tests for Subscription flow
 */

test.describe('Subscribe Page', () => {
    test('should display subscription plans', async ({ page }) => {
        await page.goto('/subscribe');

        // Should see the page header
        await expect(page.locator('h1')).toContainText('Choose Your Plan');

        // Should see plan options
        await expect(page.locator('text=Basic')).toBeVisible();
        await expect(page.locator('text=Pro')).toBeVisible();
        await expect(page.locator('text=Enterprise')).toBeVisible();
    });

    test('should highlight most popular plan', async ({ page }) => {
        await page.goto('/subscribe');

        await expect(page.locator('text=Most Popular')).toBeVisible();
    });

    test('should select a plan on click', async ({ page }) => {
        await page.goto('/subscribe');

        // Wait for plans to load
        await page.waitForSelector('text=Basic', { timeout: 10000 });

        // Click on Pro plan
        const proPlan = page.locator('[class*="rounded-2xl"]').filter({ hasText: 'Pro' });
        await proPlan.click();

        // Should show "Selected" text
        await expect(proPlan.locator('text=Selected')).toBeVisible();
    });

    test('should show payment form after plan selection', async ({ page }) => {
        await page.goto('/subscribe');

        // Click on a plan
        const basicPlan = page.locator('[class*="rounded-2xl"]').filter({ hasText: 'Basic' });
        await basicPlan.click();

        // Payment form should appear
        await expect(page.locator('h2:has-text("Complete Your Subscription")')).toBeVisible();
    });

    test('should have security badge', async ({ page }) => {
        await page.goto('/subscribe');

        // Click on a plan
        await page.locator('[class*="rounded-2xl"]').filter({ hasText: 'Basic' }).click();

        // Security notice should be visible
        await expect(page.locator('text=Secured by Stripe')).toBeVisible();
    });
});
