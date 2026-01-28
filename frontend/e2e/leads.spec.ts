import { test, expect } from '@playwright/test';

/**
 * E2E tests for Lead management (import/export)
 */

test.describe('Lead Import', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/auth/login');
        await page.fill('input[name="email"]', 'user@facemortgage.com');
        await page.fill('input[name="password"]', 'user123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/dashboard/);
    });

    test('should display lead import page', async ({ page }) => {
        await page.goto('/dashboard/leads/import');

        await expect(page.locator('h1')).toContainText('Import Leads');
    });

    test('should show CSV format guide', async ({ page }) => {
        await page.goto('/dashboard/leads/import');

        await expect(page.locator('h3:has-text("CSV Format Requirements")')).toBeVisible();
        await expect(page.locator('text=contact_name,contact_email')).toBeVisible();
    });

    test('should have file upload area', async ({ page }) => {
        await page.goto('/dashboard/leads/import');

        await expect(page.locator('text=Click to upload or drag and drop')).toBeVisible();
        await expect(page.locator('text=CSV files only')).toBeVisible();
    });

    test('should disable import button when no file selected', async ({ page }) => {
        await page.goto('/dashboard/leads/import');

        const importButton = page.locator('button:has-text("Import Leads")');
        await expect(importButton).toBeDisabled();
    });

    test('should have back navigation', async ({ page }) => {
        await page.goto('/dashboard/leads/import');

        await expect(page.locator('text=Back to Leads')).toBeVisible();
    });
});

test.describe('Lead Export', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/auth/login');
        await page.fill('input[name="email"]', 'user@facemortgage.com');
        await page.fill('input[name="password"]', 'user123');
        await page.click('button[type="submit"]');
        await page.waitForURL(/dashboard/);
    });

    test('should have export button on leads page', async ({ page }) => {
        await page.goto('/dashboard/leads');

        await expect(page.locator('button:has-text("Export")')).toBeVisible();
    });

    test('should have import link on leads page', async ({ page }) => {
        await page.goto('/dashboard/leads');

        await expect(page.locator('a:has-text("Import")')).toBeVisible();
    });
});
