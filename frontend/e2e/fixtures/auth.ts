import { Page } from '@playwright/test';

/**
 * Authentication helpers for E2E tests.
 */

// Test user credentials
export const TEST_USERS = {
  professional: {
    email: 'test-professional@example.com',
    password: 'testpassword123',
    type: 'loan_officer',
  },
  borrower: {
    email: 'test-borrower@example.com',
    password: 'testpassword123',
    type: 'borrower',
  },
};

/**
 * Login as a professional user.
 */
export async function loginAsProfessional(page: Page): Promise<void> {
  await page.goto('/auth/login');
  await page.getByLabel(/email/i).fill(TEST_USERS.professional.email);
  await page.getByLabel(/password/i).fill(TEST_USERS.professional.password);
  await page.getByRole('button', { name: /log in|sign in/i }).click();
  await page.waitForURL('**/dashboard**', { timeout: 10000 });
}

/**
 * Login as a borrower user.
 */
export async function loginAsBorrower(page: Page): Promise<void> {
  await page.goto('/auth/login');
  await page.getByLabel(/email/i).fill(TEST_USERS.borrower.email);
  await page.getByLabel(/password/i).fill(TEST_USERS.borrower.password);
  await page.getByRole('button', { name: /log in|sign in/i }).click();
  await page.waitForURL('**/', { timeout: 10000 });
}

/**
 * Logout the current user.
 */
export async function logout(page: Page): Promise<void> {
  const logoutButton = page.getByRole('button', { name: /log out|sign out/i });
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForURL('**/', { timeout: 5000 });
  }
}

/**
 * Check if user is authenticated.
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const dashboardLink = page.getByRole('link', { name: /dashboard/i });
  const logoutButton = page.getByRole('button', { name: /log out/i });

  return (await dashboardLink.isVisible()) || (await logoutButton.isVisible());
}

/**
 * Navigate to login page if not already there.
 */
export async function ensureOnLoginPage(page: Page): Promise<void> {
  if (!page.url().includes('/auth/login')) {
    await page.goto('/auth/login');
  }
}

/**
 * Wait for authentication to complete after login.
 */
export async function waitForAuth(page: Page, expectedPath?: string): Promise<void> {
  if (expectedPath) {
    await page.waitForURL(`**${expectedPath}**`, { timeout: 10000 });
  } else {
    // Wait for either dashboard or home page
    await Promise.race([
      page.waitForURL('**/dashboard**', { timeout: 10000 }),
      page.waitForURL('**/', { timeout: 10000 }),
    ]);
  }
}
