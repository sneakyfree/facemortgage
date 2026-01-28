import { test, expect } from '@playwright/test';

test.describe('SMS Settings Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/settings/sms');
    });

    test('should display SMS settings page', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /SMS Notifications/i })).toBeVisible();
    });

    test('should have phone number input', async ({ page }) => {
        await expect(page.getByPlaceholder(/555/)).toBeVisible();
    });

    test('should have verify button', async ({ page }) => {
        await expect(page.getByRole('button', { name: /verify/i })).toBeVisible();
    });

    test('should show notification toggle options', async ({ page }) => {
        await expect(page.getByText(/New Leads/i)).toBeVisible();
        await expect(page.getByText(/Missed Calls/i)).toBeVisible();
        await expect(page.getByText(/Scheduled Reminders/i)).toBeVisible();
    });

    test('should have toggle switches for each notification type', async ({ page }) => {
        const toggles = page.getByRole('switch');
        await expect(toggles).toHaveCount(3);
    });

    test('should show save button disabled when phone not verified', async ({ page }) => {
        const saveButton = page.getByRole('button', { name: /save preferences/i });
        await expect(saveButton).toBeDisabled();
    });
});

test.describe('Invoice History Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/billing/invoices');
    });

    test('should display invoices page', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /Invoice History/i })).toBeVisible();
    });

    test('should show empty state when no invoices', async ({ page }) => {
        // Either show invoices table or empty state
        const hasTable = await page.locator('table').isVisible().catch(() => false);
        const hasEmptyState = await page.getByText(/No Invoices Yet/i).isVisible().catch(() => false);
        expect(hasTable || hasEmptyState).toBeTruthy();
    });

    test('should have link to view plans', async ({ page }) => {
        // Check for either empty state CTA or invoice table
        const viewPlansLink = page.getByRole('link', { name: /view plans/i });
        const tableExists = await page.locator('table').isVisible().catch(() => false);

        if (!tableExists) {
            await expect(viewPlansLink).toBeVisible();
        }
    });
});

test.describe('Admin Users Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/admin/users');
    });

    test('should display users management page', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /User Management/i })).toBeVisible();
    });

    test('should have search input', async ({ page }) => {
        await expect(page.getByPlaceholder(/Search users/i)).toBeVisible();
    });

    test('should show users table with headers', async ({ page }) => {
        await expect(page.getByRole('columnheader', { name: /User/i })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: /Type/i })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: /Status/i })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: /Actions/i })).toBeVisible();
    });
});

test.describe('Billing Page with Usage Meter', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/billing');
    });

    test('should show usage section', async ({ page }) => {
        await expect(page.getByText(/Usage This Period/i)).toBeVisible();
    });

    test('should have quick links section', async ({ page }) => {
        await expect(page.getByText(/Quick Links/i)).toBeVisible();
    });

    test('should link to invoice history', async ({ page }) => {
        await expect(page.getByRole('link', { name: /Invoice History/i })).toBeVisible();
    });

    test('should link to notification settings', async ({ page }) => {
        await expect(page.getByRole('link', { name: /Notification Settings/i })).toBeVisible();
    });

    test('should link to privacy settings', async ({ page }) => {
        await expect(page.getByRole('link', { name: /Privacy/i })).toBeVisible();
    });
});

test.describe('Lead Score Column', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/leads');
    });

    test('should have score column header', async ({ page }) => {
        await expect(page.getByRole('columnheader', { name: /Score/i })).toBeVisible();
    });
});

test.describe('Partnerships Payout', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard/partnerships');
    });

    test('should display partnerships page', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /Partnerships/i })).toBeVisible();
    });

    test('should show stats cards', async ({ page }) => {
        await expect(page.getByText(/Active Partners/i)).toBeVisible();
        await expect(page.getByText(/Total Referrals/i)).toBeVisible();
        await expect(page.getByText(/Total Earnings/i)).toBeVisible();
    });

    test('should have partners and referrals tabs', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Partners/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /Referrals/i })).toBeVisible();
    });

    test('should have invite partner button', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Invite Partner/i })).toBeVisible();
    });
});
