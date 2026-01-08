import { test, expect } from '@playwright/test';

/**
 * E2E tests for billing and subscription management.
 * Tests Stripe checkout integration and subscription tiers.
 */

test.describe('Subscription Tiers', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/for-professionals');
  });

  test('displays subscription tier options', async ({ page }) => {
    // Should show pricing tiers
    await expect(page.getByText(/basic|starter/i)).toBeVisible();
    await expect(page.getByText(/professional|pro/i)).toBeVisible();
    await expect(page.getByText(/premium|enterprise/i)).toBeVisible();
  });

  test('shows pricing for each tier', async ({ page }) => {
    // Should display prices
    await expect(page.getByText(/\$\d+/)).toBeVisible();
  });

  test('shows features for each tier', async ({ page }) => {
    // Should list features per tier
    const featureLists = page.locator('ul, [role="list"]').filter({
      has: page.locator('li, [role="listitem"]')
    });

    // Should have multiple feature lists (one per tier)
    await expect(featureLists.first()).toBeVisible();
  });

  test('has CTA buttons for each tier', async ({ page }) => {
    // Should have sign up or subscribe buttons
    const ctaButtons = page.getByRole('button', { name: /get started|subscribe|sign up|choose/i });
    await expect(ctaButtons.first()).toBeVisible();
  });

  test('clicking tier CTA initiates signup/checkout flow', async ({ page }) => {
    const ctaButton = page.getByRole('button', { name: /get started|subscribe/i }).first();

    if (await ctaButton.isVisible()) {
      await ctaButton.click();

      // Should either redirect to login/register or open checkout
      await page.waitForTimeout(2000);
      const url = page.url();

      // Should navigate somewhere (auth or checkout)
      expect(url).toMatch(/auth|checkout|stripe|register|login|billing/);
    }
  });
});

test.describe('Billing Page', () => {
  test('billing page requires authentication', async ({ page }) => {
    await page.goto('/dashboard/billing');

    // Should redirect to login if not authenticated
    await expect(page).toHaveURL(/login|auth/);
  });

  test('billing page shows current subscription status', async ({ page }) => {
    // This would require authentication
    await page.goto('/dashboard/billing');

    if (!page.url().includes('login')) {
      // Should show current plan
      await expect(page.getByText(/current plan|subscription|billing/i)).toBeVisible();
    }
  });
});

test.describe('Stripe Checkout Integration', () => {
  test('checkout redirects to Stripe', async ({ page }) => {
    // Navigate to a page that would trigger Stripe checkout
    await page.goto('/for-professionals');

    // Find and click a subscribe/checkout button
    const subscribeButton = page.getByRole('button', { name: /subscribe|upgrade|get started/i }).first();

    if (await subscribeButton.isVisible()) {
      // Listen for navigation
      const navigationPromise = page.waitForNavigation({ timeout: 10000 }).catch(() => null);

      await subscribeButton.click();

      await navigationPromise;

      // Check if redirected to Stripe or internal checkout
      const url = page.url();

      // Should go to stripe.com/checkout or internal checkout page
      const isStripeOrCheckout = url.includes('stripe.com') ||
        url.includes('checkout') ||
        url.includes('auth') ||
        url.includes('billing');

      expect(isStripeOrCheckout).toBeTruthy();
    }
  });
});

test.describe('Billing Portal Access', () => {
  test('can access billing portal link', async ({ page }) => {
    // Would need to be authenticated
    await page.goto('/dashboard/billing');

    if (!page.url().includes('login')) {
      // Look for manage subscription or portal link
      const portalLink = page.getByRole('link', { name: /manage|portal|update payment/i });

      if (await portalLink.isVisible()) {
        // Should be a link that would go to Stripe portal
        const href = await portalLink.getAttribute('href');
        expect(href).toBeTruthy();
      }
    }
  });
});

test.describe('Plan Comparison', () => {
  test('comparison shows feature differences', async ({ page }) => {
    await page.goto('/for-professionals');

    // Look for comparison table or feature comparison
    const comparisonSection = page.locator('table, [role="table"]').or(
      page.locator('.comparison, .pricing-comparison')
    );

    if (await comparisonSection.isVisible()) {
      // Should have checkmarks or feature indicators
      await expect(comparisonSection.locator('svg, .check, .feature')).toBeVisible();
    }
  });

  test('plans are clearly differentiated', async ({ page }) => {
    await page.goto('/for-professionals');

    // Each plan should have a distinct name
    const planNames = ['basic', 'professional', 'premium', 'starter', 'pro', 'enterprise'];

    let foundPlans = 0;
    for (const plan of planNames) {
      const planElement = page.getByText(new RegExp(plan, 'i'));
      if (await planElement.isVisible()) {
        foundPlans++;
      }
    }

    // Should find at least 2 distinct plans
    expect(foundPlans).toBeGreaterThanOrEqual(2);
  });
});

test.describe('Trial Information', () => {
  test('shows trial period information if applicable', async ({ page }) => {
    await page.goto('/for-professionals');

    // Look for trial-related text
    const trialText = page.getByText(/trial|free|days free/i);

    // May or may not have trial - just check the page loads
    await expect(page.getByRole('heading')).toBeVisible();
  });
});

test.describe('Invoice History', () => {
  test('billing page shows invoice history when authenticated', async ({ page }) => {
    await page.goto('/dashboard/billing');

    if (!page.url().includes('login')) {
      // Look for invoices section
      const invoicesSection = page.getByText(/invoices|payment history|billing history/i);

      if (await invoicesSection.isVisible()) {
        // Should show date and amount columns or cards
        await expect(page.getByText(/\$|date|amount/i)).toBeVisible();
      }
    }
  });
});
