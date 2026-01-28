import { test, expect } from '@playwright/test';

/**
 * Demo Confidence Smoke Tests
 *
 * Minimal test suite for quick verification before investor demos.
 * Run with: npx playwright test e2e/demo-smoke.spec.ts
 */

test.describe('Demo Smoke Tests', () => {

    test('Homepage loads successfully', async ({ page }) => {
        await page.goto('/');

        // Page should load without errors
        await expect(page).toHaveTitle(/.*/);

        // Should have an h1 heading
        await expect(page.locator('h1').first()).toBeVisible();
    });

    test('Get Matched page loads', async ({ page }) => {
        await page.goto('/get-matched');

        // Heading should be visible
        await expect(page.locator('h1, h2').first()).toBeVisible();

        // Should have page content
        await expect(page.locator('body')).not.toBeEmpty();
    });

    test('Login page exists', async ({ page }) => {
        const response = await page.goto('/auth/login');

        // Should return 200 (page exists)
        expect(response?.status()).toBeLessThan(400);
    });

    test('Register page exists', async ({ page }) => {
        const response = await page.goto('/auth/register');

        // Should return 200 (page exists)
        expect(response?.status()).toBeLessThan(400);
    });

    test('No JavaScript errors on homepage', async ({ page }) => {
        const errors: string[] = [];
        page.on('pageerror', error => errors.push(error.message));

        await page.goto('/');
        await page.waitForTimeout(2000);

        // Should have no critical JS errors (filter out minor warnings)
        const criticalErrors = errors.filter(e =>
            !e.includes('ResizeObserver') &&
            !e.includes('Non-Error promise rejection')
        );
        expect(criticalErrors).toHaveLength(0);
    });

    test('No console errors on get-matched page', async ({ page }) => {
        const errors: string[] = [];
        page.on('pageerror', error => errors.push(error.message));

        await page.goto('/get-matched');
        await page.waitForTimeout(2000);

        const criticalErrors = errors.filter(e =>
            !e.includes('ResizeObserver') &&
            !e.includes('Non-Error promise rejection')
        );
        expect(criticalErrors).toHaveLength(0);
    });
});
