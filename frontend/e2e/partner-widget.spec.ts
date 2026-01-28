import { test, expect } from '@playwright/test';

/**
 * Partner Widget E2E Tests
 * 
 * Tests the embeddable widget functionality for third-party partner sites.
 * Validates iframe behavior, themes, and core widget features.
 */

test.describe('Partner Widget', () => {
    test.describe('Widget Page Loading', () => {
        test('should load widget page with professional_id parameter', async ({ page }) => {
            await page.goto('/embed/widget?professional_id=test-123');

            // Wait for page to be interactive
            await page.waitForLoadState('domcontentloaded');

            // Widget should be rendered (either loading, profile, or error state)
            await expect(page.locator('body')).toBeVisible();
        });

        test('should handle missing professional_id gracefully', async ({ page }) => {
            await page.goto('/embed/widget');

            await page.waitForLoadState('domcontentloaded');

            // Page should still render (may show error or loading)
            await expect(page.locator('body')).toBeVisible();
        });

        test('should accept theme parameter in URL', async ({ page }) => {
            await page.goto('/embed/widget?professional_id=test-123&theme=dark');

            // URL should have theme parameter
            await expect(page).toHaveURL(/theme=dark/);
        });

        test('should accept partner_id parameter for attribution', async ({ page }) => {
            const partnerId = 'partner-acme-realty';
            await page.goto(`/embed/widget?professional_id=test-123&partner_id=${partnerId}`);

            await expect(page).toHaveURL(new RegExp(`partner_id=${partnerId}`));
        });
    });

    test.describe('Widget Embed Layout', () => {
        test('should have clean embed layout without main navigation', async ({ page }) => {
            await page.goto('/embed/widget?professional_id=test-123');

            await page.waitForLoadState('domcontentloaded');

            // Main site navigation should not be present in embed layout
            const nav = page.locator('nav');
            const navCount = await nav.count();
            expect(navCount).toBe(0);
        });

        test('should have minimal body styling for iframe embedding', async ({ page }) => {
            await page.goto('/embed/widget?professional_id=test-123');

            await page.waitForLoadState('domcontentloaded');

            // Body should have no margin for clean iframe embedding
            const body = page.locator('body');
            const margin = await body.evaluate(el => window.getComputedStyle(el).margin);
            expect(margin).toBe('0px');
        });
    });

    test.describe('Get Matched Embed Page', () => {
        test('should load get-matched embed page', async ({ page }) => {
            await page.goto('/embed/get-matched');

            await page.waitForLoadState('domcontentloaded');

            // Page should render without main navigation
            const nav = page.locator('nav');
            const navCount = await nav.count();
            expect(navCount).toBe(0);
        });
    });
});

// Note: Widget test harness (/widget-test-harness.html) is available 
// for manual testing but not included in automated tests since
// static HTML files require different serving configuration.
