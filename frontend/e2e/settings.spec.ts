import { test, expect } from '@playwright/test';

/**
 * E2E tests for Settings pages (notifications, privacy)
 */

test.describe('Notification Settings', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/auth/login');
        await page.fill('input[name="email"]', 'user@facemortgage.com');
        await page.fill('input[name="password"]', 'user123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/dashboard/);
    });

    test('should display notification preferences page', async ({ page }) => {
        await page.goto('/dashboard/settings/notifications');

        await expect(page.locator('h1')).toContainText('Notification Preferences');
    });

    test('should show email notification toggles', async ({ page }) => {
        await page.goto('/dashboard/settings/notifications');

        // Should have email section
        await expect(page.locator('h2:has-text("Email Notifications")')).toBeVisible();

        // Should have toggle buttons
        const toggles = page.locator('button[role="switch"]');
        await expect(toggles.first()).toBeVisible();
    });

    test('should toggle notification settings', async ({ page }) => {
        await page.goto('/dashboard/settings/notifications');

        // Find the first toggle
        const toggle = page.locator('button[role="switch"]').first();
        const initialState = await toggle.getAttribute('aria-checked');

        // Click to toggle
        await toggle.click();

        // State should change
        const newState = await toggle.getAttribute('aria-checked');
        expect(newState).not.toEqual(initialState);
    });

    test('should have save button', async ({ page }) => {
        await page.goto('/dashboard/settings/notifications');

        await expect(page.locator('button:has-text("Save Preferences")')).toBeVisible();
    });
});

test.describe('Privacy Settings', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/auth/login');
        await page.fill('input[name="email"]', 'user@facemortgage.com');
        await page.fill('input[name="password"]', 'user123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/dashboard/);
    });

    test('should display privacy settings page', async ({ page }) => {
        await page.goto('/dashboard/settings/privacy');

        await expect(page.locator('h1')).toContainText('Privacy & Data');
    });

    test('should have data export section', async ({ page }) => {
        await page.goto('/dashboard/settings/privacy');

        await expect(page.locator('h2:has-text("Download Your Data")')).toBeVisible();
        await expect(page.locator('button:has-text("Request Data Export")')).toBeVisible();
    });

    test('should have account deletion section', async ({ page }) => {
        await page.goto('/dashboard/settings/privacy');

        await expect(page.locator('h2:has-text("Delete Account")')).toBeVisible();
        await expect(page.locator('button:has-text("Delete My Account")')).toBeVisible();
    });

    test('should show confirmation dialog for account deletion', async ({ page }) => {
        await page.goto('/dashboard/settings/privacy');

        // Click delete button
        await page.click('button:has-text("Delete My Account")');

        // Confirmation should appear
        await expect(page.locator('text=Are you absolutely sure')).toBeVisible();
        await expect(page.locator('input[placeholder="DELETE"]')).toBeVisible();
    });
});
