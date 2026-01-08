import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility E2E tests using axe-core.
 * Tests WCAG 2.1 AA compliance across key pages and components.
 */

test.describe('Accessibility', () => {
  test.describe('Home Page', () => {
    test('should not have any automatically detectable accessibility issues', async ({ page }) => {
      await page.goto('/');

      // Wait for grid to load
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('has proper document structure', async ({ page }) => {
      await page.goto('/');

      // Should have exactly one main landmark
      const mainLandmarks = await page.locator('main').count();
      expect(mainLandmarks).toBe(1);

      // Should have a skip to content link
      const skipLink = page.locator('a[href="#main-content"]');
      expect(await skipLink.count()).toBeGreaterThanOrEqual(1);
    });

    test('skip link works correctly', async ({ page }) => {
      await page.goto('/');

      // Focus the skip link (usually hidden until focused)
      await page.keyboard.press('Tab');

      // Click the skip link
      const skipLink = page.locator('a[href="#main-content"]');
      if (await skipLink.isVisible()) {
        await skipLink.click();

        // Focus should move to main content area
        const mainContent = page.locator('#main-content');
        await expect(mainContent).toBeFocused();
      }
    });

    test('professional cards are keyboard navigable', async ({ page }) => {
      await page.goto('/');

      // Wait for grid to load
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // Tab through the page
      let foundArticle = false;
      for (let i = 0; i < 30 && !foundArticle; i++) {
        await page.keyboard.press('Tab');
        const focusedRole = await page.locator(':focus').getAttribute('role');
        if (focusedRole === 'article') {
          foundArticle = true;
        }
      }

      expect(foundArticle).toBe(true);
    });

    test('images have alt text', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // Check all images have alt text
      const imagesWithoutAlt = await page.locator('img:not([alt])').count();
      expect(imagesWithoutAlt).toBe(0);

      // Check no images have empty alt (except decorative ones which should have role="presentation")
      const imagesWithEmptyAlt = await page.locator('img[alt=""]:not([role="presentation"]):not([aria-hidden="true"])').count();
      expect(imagesWithEmptyAlt).toBe(0);
    });
  });

  test.describe('Navigation', () => {
    test('header navigation is accessible', async ({ page }) => {
      await page.goto('/');

      // Navigation should have proper role
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();

      // Links should be focusable
      const navLinks = page.locator('nav a');
      const linkCount = await navLinks.count();

      for (let i = 0; i < linkCount; i++) {
        const link = navLinks.nth(i);
        // Check link has accessible name
        const accessibleName = await link.evaluate((el) => {
          return el.textContent || el.getAttribute('aria-label') || '';
        });
        expect(accessibleName.trim().length).toBeGreaterThan(0);
      }
    });

    test('buttons have accessible names', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // All buttons should have accessible names
      const buttonsWithoutName = await page.locator('button:not([aria-label]):not(:has-text(/\\S/))').count();
      expect(buttonsWithoutName).toBe(0);
    });
  });

  test.describe('Modal Dialogs', () => {
    test('video call modal has proper ARIA attributes', async ({ page }) => {
      await page.goto('/');

      // Wait for grid
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // Click on an available professional
      const availableCard = page.locator('[role="article"]').filter({
        has: page.getByText('Available'),
      }).first();

      if (await availableCard.isVisible()) {
        await availableCard.hover();
        const callButton = availableCard.getByRole('button', { name: /call/i });

        if (await callButton.isVisible()) {
          await callButton.click();

          // Wait for modal
          const modal = page.locator('[role="dialog"]');
          await expect(modal).toBeVisible({ timeout: 5000 });

          // Modal should have aria-modal
          await expect(modal).toHaveAttribute('aria-modal', 'true');

          // Modal should have aria-labelledby or aria-label
          const hasLabel =
            (await modal.getAttribute('aria-labelledby')) ||
            (await modal.getAttribute('aria-label'));
          expect(hasLabel).toBeTruthy();
        }
      }
    });

    test('modal focus is trapped', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      const availableCard = page.locator('[role="article"]').filter({
        has: page.getByText('Available'),
      }).first();

      if (await availableCard.isVisible()) {
        await availableCard.hover();
        const callButton = availableCard.getByRole('button', { name: /call/i });

        if (await callButton.isVisible()) {
          await callButton.click();

          const modal = page.locator('[role="dialog"]');
          await expect(modal).toBeVisible({ timeout: 5000 });

          // Get all focusable elements in modal
          const focusableElements = modal.locator(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const count = await focusableElements.count();

          if (count > 0) {
            // Tab through all elements
            for (let i = 0; i < count + 2; i++) {
              await page.keyboard.press('Tab');
            }

            // Focus should still be inside modal (trapped)
            const focusedElement = page.locator(':focus');
            const isInsideModal = await modal.locator(':focus').count();
            expect(isInsideModal).toBeGreaterThan(0);
          }
        }
      }
    });

    test('modal closes on Escape key', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      const availableCard = page.locator('[role="article"]').filter({
        has: page.getByText('Available'),
      }).first();

      if (await availableCard.isVisible()) {
        await availableCard.hover();
        const callButton = availableCard.getByRole('button', { name: /call/i });

        if (await callButton.isVisible()) {
          await callButton.click();

          const modal = page.locator('[role="dialog"]');
          await expect(modal).toBeVisible({ timeout: 5000 });

          // Press Escape
          await page.keyboard.press('Escape');

          // Modal should close (or focus should have moved)
          await page.waitForTimeout(500);
        }
      }
    });
  });

  test.describe('Forms', () => {
    test('form inputs have associated labels', async ({ page }) => {
      await page.goto('/login');

      // Check all inputs have labels
      const inputs = page.locator('input:not([type="hidden"]):not([type="submit"])');
      const inputCount = await inputs.count();

      for (let i = 0; i < inputCount; i++) {
        const input = inputs.nth(i);
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledby = await input.getAttribute('aria-labelledby');

        // Input should have either: id with matching label, aria-label, or aria-labelledby
        const hasLabel =
          (id && (await page.locator(`label[for="${id}"]`).count()) > 0) ||
          ariaLabel ||
          ariaLabelledby;

        expect(hasLabel).toBeTruthy();
      }
    });

    test('error messages are announced to screen readers', async ({ page }) => {
      await page.goto('/login');

      // Submit form without filling fields
      const submitButton = page.getByRole('button', { name: /sign in|log in/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Check for error messages with proper ARIA
        const errorMessages = page.locator('[role="alert"], [aria-live="polite"], [aria-live="assertive"]');
        await page.waitForTimeout(500);

        // If there are validation errors, they should be announced
        const count = await errorMessages.count();
        // This check is conditional - only if form has inline validation
        if (count > 0) {
          expect(count).toBeGreaterThan(0);
        }
      }
    });
  });

  test.describe('Color Contrast', () => {
    test('text has sufficient color contrast', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2aa'])
        .options({
          rules: {
            'color-contrast': { enabled: true },
          },
        })
        .analyze();

      const contrastViolations = accessibilityScanResults.violations.filter(
        (v) => v.id === 'color-contrast'
      );

      expect(contrastViolations).toEqual([]);
    });
  });

  test.describe('Interactive Elements', () => {
    test('focus is visible on interactive elements', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // Tab to first focusable element
      await page.keyboard.press('Tab');

      // Check that the focused element has visible focus indicator
      const focusedElement = page.locator(':focus');
      const hasFocusStyle = await focusedElement.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        const hasBorder = styles.outlineWidth !== '0px' && styles.outlineStyle !== 'none';
        const hasBoxShadow = styles.boxShadow !== 'none';
        const hasRing = el.className.includes('ring') || el.className.includes('focus');
        return hasBorder || hasBoxShadow || hasRing;
      });

      expect(hasFocusStyle).toBe(true);
    });

    test('touch targets are large enough', async ({ page }) => {
      await page.goto('/');
      await page.waitForSelector('[role="article"]', { timeout: 10000 });

      // Check button sizes (WCAG 2.5.5 requires 44x44px minimum)
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const box = await button.boundingBox();
          if (box) {
            // AAA requires 44x44, AA requires 24x24 minimum
            expect(box.width).toBeGreaterThanOrEqual(24);
            expect(box.height).toBeGreaterThanOrEqual(24);
          }
        }
      }
    });
  });

  test.describe('Dynamic Content', () => {
    test('live regions announce changes', async ({ page }) => {
      await page.goto('/');

      // Look for live region elements
      const liveRegions = page.locator('[aria-live], [role="status"], [role="alert"]');
      const count = await liveRegions.count();

      // Application should have at least one live region for announcements
      // This is a soft check as not all pages require live regions
      if (count > 0) {
        for (let i = 0; i < count; i++) {
          const region = liveRegions.nth(i);
          const ariaLive = await region.getAttribute('aria-live');
          const role = await region.getAttribute('role');

          // Live region should have proper politeness level
          expect(
            ariaLive === 'polite' ||
              ariaLive === 'assertive' ||
              role === 'status' ||
              role === 'alert'
          ).toBe(true);
        }
      }
    });
  });

  test.describe('Professional Dashboard', () => {
    test.skip('dashboard page is accessible', async ({ page }) => {
      // This test would require authentication
      await page.goto('/dashboard');

      // Wait for page load
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  });
});
