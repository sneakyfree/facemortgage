import { test, expect } from '@playwright/test';

/**
 * E2E tests for the home page and professional grid.
 */
test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('has correct title', async ({ page }) => {
    await expect(page).toHaveTitle(/FaceMortgage/);
  });

  test('displays header with logo and navigation', async ({ page }) => {
    // Logo should be visible
    await expect(page.getByText('FaceMortgage')).toBeVisible();

    // Navigation links should be present
    await expect(page.getByRole('link', { name: 'Find Professionals' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'How It Works' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'For Professionals' })).toBeVisible();
  });

  test('shows login and signup buttons when not authenticated', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Log In' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Sign Up' })).toBeVisible();
  });

  test('displays filter panel', async ({ page }) => {
    await expect(page.getByText('Find Your Professional')).toBeVisible();

    // Check for filter dropdowns
    await expect(page.getByText('State')).toBeVisible();
    await expect(page.getByText('Professional Type')).toBeVisible();
    await expect(page.getByText('Language')).toBeVisible();
    await expect(page.getByText('Specialty')).toBeVisible();
    await expect(page.getByText('Minimum Rating')).toBeVisible();
  });

  test('filter panel has all professional type options', async ({ page }) => {
    const typeSelect = page.locator('select').nth(1);
    await typeSelect.click();

    await expect(page.getByText('All Types')).toBeVisible();
    await expect(page.getByText('Loan Officer')).toBeVisible();
    await expect(page.getByText('Realtor')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('logo links to home page', async ({ page }) => {
    await page.goto('/how-it-works');
    await page.getByRole('link', { name: 'FaceMortgage' }).click();
    await expect(page).toHaveURL('/');
  });

  test('login link navigates to login page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Log In' }).click();
    await expect(page).toHaveURL('/auth/login');
  });

  test('signup link navigates to register page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Sign Up' }).click();
    await expect(page).toHaveURL('/auth/register');
  });
});
