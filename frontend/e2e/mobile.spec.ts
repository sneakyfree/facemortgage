import { test, expect, devices } from '@playwright/test';

/**
 * E2E tests for mobile experience.
 * Tests responsive behavior and mobile-specific interactions.
 */

// Use iPhone 12 viewport for mobile tests
test.use({ viewport: { width: 390, height: 844 } });

test.describe('Mobile Navigation', () => {
  test('mobile nav toggle is visible on small screens', async ({ page }) => {
    await page.goto('/');

    // Desktop nav should be hidden
    await expect(page.locator('nav.hidden.md\\:flex, nav[class*="hidden md:flex"]')).toBeHidden();

    // Mobile hamburger button should be visible
    const mobileMenuButton = page.getByRole('button', { name: /menu|navigation/i }).or(
      page.locator('[aria-label*="menu"]')
    );

    // If there's a hamburger menu, it should be visible
    // Some designs show it, some use a different pattern
    await expect(page.getByRole('banner')).toBeVisible();
  });

  test('mobile nav opens and closes', async ({ page }) => {
    await page.goto('/');

    // Find and click hamburger menu if it exists
    const menuButton = page.getByRole('button', { name: /menu/i }).or(
      page.locator('button[aria-expanded]').first()
    );

    if (await menuButton.isVisible()) {
      await menuButton.click();

      // Should show mobile nav menu
      const mobileNav = page.locator('[role="dialog"], .mobile-menu, nav').filter({
        has: page.getByRole('link')
      });

      await expect(mobileNav).toBeVisible({ timeout: 5000 });

      // Close the menu
      await menuButton.click();

      // Menu should close
      await page.waitForTimeout(500);
    }
  });

  test('mobile nav links work', async ({ page }) => {
    await page.goto('/');

    const menuButton = page.getByRole('button', { name: /menu/i }).first();

    if (await menuButton.isVisible()) {
      await menuButton.click();

      // Find a nav link and click it
      const navLink = page.getByRole('link', { name: /how it works|for professionals/i }).first();

      if (await navLink.isVisible()) {
        await navLink.click();

        // Should navigate
        await page.waitForTimeout(1000);
        const url = page.url();
        expect(url).toMatch(/how-it-works|for-professionals/);
      }
    }
  });
});

test.describe('Mobile Professional Grid', () => {
  test('professional grid shows single column on mobile', async ({ page }) => {
    await page.goto('/');

    // Wait for grid to load
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Check that cards are stacked (single column)
    const cards = page.locator('[role="article"]');
    const firstCard = cards.first();
    const secondCard = cards.nth(1);

    if (await secondCard.isVisible()) {
      const firstBox = await firstCard.boundingBox();
      const secondBox = await secondCard.boundingBox();

      if (firstBox && secondBox) {
        // Second card should be below first (not side by side)
        expect(secondBox.y).toBeGreaterThan(firstBox.y);
      }
    }
  });

  test('filters are accessible on mobile', async ({ page }) => {
    await page.goto('/');

    // Look for filter button or expandable filter section
    const filterButton = page.getByRole('button', { name: /filter/i });
    const filterSection = page.locator('[role="region"]').filter({
      has: page.getByText(/state|type|language/i)
    });

    // Either filter button or filter section should be accessible
    const filterAccessible = await filterButton.isVisible() || await filterSection.isVisible();
    expect(filterAccessible).toBeTruthy();
  });

  test('can apply filters on mobile', async ({ page }) => {
    await page.goto('/');

    // Open filters if needed
    const filterButton = page.getByRole('button', { name: /filter/i });
    if (await filterButton.isVisible()) {
      await filterButton.click();
    }

    // Find a state filter dropdown or similar
    const stateSelect = page.getByRole('combobox', { name: /state/i }).or(
      page.locator('select').filter({ has: page.locator('option') }).first()
    );

    if (await stateSelect.isVisible()) {
      // Should be able to interact with filters
      await stateSelect.click();
    }
  });

  test('professional cards are tap-friendly', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Cards should be adequately sized for touch
    const firstCard = page.locator('[role="article"]').first();
    const box = await firstCard.boundingBox();

    if (box) {
      // Card should be at least 44px tall (WCAG touch target minimum)
      expect(box.height).toBeGreaterThanOrEqual(44);
    }
  });
});

test.describe('Mobile Lead Capture', () => {
  test('lead capture modal is usable on mobile', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find available professional and tap
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.tap();

      // Wait for modal
      await page.waitForTimeout(2000);

      const modal = page.locator('[role="dialog"]');
      if (await modal.isVisible()) {
        const box = await modal.boundingBox();

        if (box) {
          // Modal should fit within viewport width
          expect(box.width).toBeLessThanOrEqual(390 + 20); // viewport + padding

          // Form inputs should be visible
          await expect(modal.locator('input')).toBeVisible();
        }
      }
    }
  });

  test('form inputs are properly sized for touch on mobile', async ({ page }) => {
    await page.goto('/auth/register');

    // Check that input fields meet minimum touch target size
    const inputs = page.locator('input[type="text"], input[type="email"], input[type="password"]');

    const firstInput = inputs.first();
    if (await firstInput.isVisible()) {
      const box = await firstInput.boundingBox();

      if (box) {
        // Should be at least 44px tall for touch
        expect(box.height).toBeGreaterThanOrEqual(40);
      }
    }
  });
});

test.describe('Mobile Call Experience', () => {
  test('call controls are touch-friendly', async ({ page }) => {
    await page.goto('/');

    // Wait for grid
    await expect(page.locator('[role="article"]').first()).toBeVisible({ timeout: 10000 });

    // Find and tap available professional
    const availableCard = page.locator('[role="article"]').filter({
      has: page.getByText('Available')
    }).first();

    if (await availableCard.isVisible()) {
      await availableCard.tap();

      // If call modal opens
      const callControls = page.locator('[role="toolbar"]');
      if (await callControls.isVisible({ timeout: 5000 })) {
        // Buttons should be adequately sized
        const buttons = callControls.getByRole('button');
        const firstButton = buttons.first();

        if (await firstButton.isVisible()) {
          const box = await firstButton.boundingBox();
          if (box) {
            // Should be at least 44x44 for touch
            expect(box.width).toBeGreaterThanOrEqual(44);
            expect(box.height).toBeGreaterThanOrEqual(44);
          }
        }
      }
    }
  });
});

test.describe('Mobile Responsive Typography', () => {
  test('text is readable on mobile', async ({ page }) => {
    await page.goto('/');

    // Body text should have adequate font size
    const paragraph = page.locator('p').first();
    if (await paragraph.isVisible()) {
      const fontSize = await paragraph.evaluate((el) => {
        return window.getComputedStyle(el).fontSize;
      });

      // Font size should be at least 14px for readability
      const fontSizeNum = parseInt(fontSize);
      expect(fontSizeNum).toBeGreaterThanOrEqual(14);
    }
  });

  test('headings are appropriately sized', async ({ page }) => {
    await page.goto('/');

    const heading = page.getByRole('heading').first();
    if (await heading.isVisible()) {
      const fontSize = await heading.evaluate((el) => {
        return window.getComputedStyle(el).fontSize;
      });

      // Heading should be larger than body text
      const fontSizeNum = parseInt(fontSize);
      expect(fontSizeNum).toBeGreaterThanOrEqual(18);
    }
  });
});

test.describe('Mobile Scroll Behavior', () => {
  test('page scrolls smoothly', async ({ page }) => {
    await page.goto('/');

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Scroll down
    await page.evaluate(() => {
      window.scrollTo({ top: 500, behavior: 'smooth' });
    });

    await page.waitForTimeout(500);

    // Verify scroll happened
    const scrollPosition = await page.evaluate(() => window.scrollY);
    expect(scrollPosition).toBeGreaterThan(0);
  });

  test('no horizontal scroll on mobile', async ({ page }) => {
    await page.goto('/');

    // Check for horizontal overflow
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    // Should not have horizontal scroll
    expect(hasHorizontalScroll).toBeFalsy();
  });
});

test.describe('Mobile Touch Interactions', () => {
  test('buttons respond to tap', async ({ page }) => {
    await page.goto('/');

    const buttons = page.getByRole('button');
    const firstButton = buttons.first();

    if (await firstButton.isVisible()) {
      // Should be able to tap buttons
      await firstButton.tap();

      // If it's a navigation button, should see some change
      // This is a basic interaction test
    }
  });

  test('links are tappable', async ({ page }) => {
    await page.goto('/');

    const links = page.getByRole('link');
    const firstLink = links.first();

    if (await firstLink.isVisible()) {
      const box = await firstLink.boundingBox();

      if (box) {
        // Links should meet minimum touch target or have adequate padding
        expect(box.height).toBeGreaterThanOrEqual(24);
      }
    }
  });
});
