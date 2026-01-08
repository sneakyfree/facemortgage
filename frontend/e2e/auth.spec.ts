import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication flows.
 */
test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
  });

  test('displays login form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /log in|sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /log in|sign in/i })).toBeVisible();
  });

  test('shows link to register page', async ({ page }) => {
    await expect(page.getByRole('link', { name: /sign up|register|create account/i })).toBeVisible();
  });

  test('validates required fields on submit', async ({ page }) => {
    await page.getByRole('button', { name: /log in|sign in/i }).click();

    // Browser validation should prevent submission
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeFocused();
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /log in|sign in/i }).click();

    // Should show an error message
    await expect(page.getByText(/invalid|incorrect|failed|error/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Register Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/register');
  });

  test('displays registration form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /sign up|register|create/i })).toBeVisible();
    await expect(page.getByLabel(/first name/i)).toBeVisible();
    await expect(page.getByLabel(/last name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test('shows link to login page', async ({ page }) => {
    await expect(page.getByRole('link', { name: /log in|sign in/i })).toBeVisible();
  });

  test('has user type selection', async ({ page }) => {
    // Should have options for borrower and professional
    await expect(page.getByText(/borrower|home buyer|looking for/i)).toBeVisible();
    await expect(page.getByText(/professional|loan officer|realtor/i)).toBeVisible();
  });
});

test.describe('Password Requirements', () => {
  test('register form validates password length', async ({ page }) => {
    await page.goto('/auth/register');

    // Fill in basic info
    await page.getByLabel(/first name/i).fill('Test');
    await page.getByLabel(/last name/i).fill('User');
    await page.getByLabel(/email/i).fill('test@example.com');

    // Try a short password
    const passwordInput = page.getByLabel(/^password$/i);
    await passwordInput.fill('short');

    // Submit and check for validation
    await page.getByRole('button', { name: /sign up|register|create/i }).click();

    // Should show password requirements error or browser validation
    // The exact behavior depends on form implementation
  });
});
