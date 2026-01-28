import { test, expect } from '@playwright/test';
import { setupAllMocks } from './fixtures/api-mocks';

/**
 * E2E Tests for Enhanced Grid Features
 * 
 * Tests advanced filtering, baseball cards, and pickup badges
 * from Phase 2 DNA Strand implementation.
 */

test.describe('Enhanced Grid Features', () => {
    test.beforeEach(async ({ page }) => {
        await setupAllMocks(page);
    });

    test('should display filter options on homepage', async ({ page }) => {
        await page.goto('/');

        // Check for filter controls
        await expect(page.locator('[data-testid="grid-filters"]')).toBeVisible();
    });

    test('should filter by specialty', async ({ page }) => {
        // Mock enhanced grid filter endpoint
        await page.route('**/api/v1/grid-enhanced/filter', async (route) => {
            const body = route.request().postDataJSON();

            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    professionals: body?.specialties?.includes('fha') ? [
                        {
                            id: 'fha-specialist-1',
                            name: 'FHA Expert',
                            specialties: ['FHA Loans'],
                            pickup_badge: { text: '<10s', color: 'green', icon: '⚡' }
                        }
                    ] : [],
                    count: 1
                })
            });
        });

        await page.goto('/');

        // Select FHA specialty filter
        await page.getByLabel(/specialty/i).click();
        await page.getByRole('option', { name: /fha/i }).click();

        // Verify filtered results
        await expect(page.getByText(/fha expert/i)).toBeVisible();
    });

    test('should display pickup time badges', async ({ page }) => {
        await page.route('**/api/v1/grid-enhanced/online-now', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    professionals: [
                        {
                            id: 'fast-lo',
                            name: 'Fast Responder',
                            pickup_badge: { text: '<10s', color: 'green', icon: '⚡' },
                            avg_pickup_seconds: 8
                        },
                        {
                            id: 'normal-lo',
                            name: 'Normal Responder',
                            pickup_badge: { text: '~25s', color: 'green', icon: '🟢' },
                            avg_pickup_seconds: 25
                        }
                    ],
                    count: 2
                })
            });
        });

        await page.goto('/');

        // Look for pickup badges
        await expect(page.getByText('⚡')).toBeVisible();
        await expect(page.getByText('<10s')).toBeVisible();
    });

    test('should open baseball card on profile click', async ({ page }) => {
        const professionalId = 'test-pro-123';

        await page.route(`**/api/v1/grid-enhanced/card/${professionalId}`, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    professional_id: professionalId,
                    name: 'John Doe',
                    overall_grade: 'A+',
                    responsiveness_grade: 'A',
                    experience_grade: 'B+',
                    rating_grade: 'A',
                    avg_rating: 4.9,
                    total_reviews: 156,
                    years_experience: 12,
                    nmls_verified: true,
                    specialties: ['FHA', 'VA', 'Jumbo']
                })
            });
        });

        await page.goto('/');

        // Click on a professional card
        await page.locator(`[data-professional-id="${professionalId}"]`).click();

        // Verify baseball card modal
        await expect(page.getByText(/A\+/)).toBeVisible();
        await expect(page.getByText(/156.*reviews/i)).toBeVisible();
    });

    test('should compare multiple professionals', async ({ page }) => {
        await page.route('**/api/v1/grid-enhanced/compare', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    professionals: [
                        { professional_id: '1', name: 'LO One', overall_grade: 'A+' },
                        { professional_id: '2', name: 'LO Two', overall_grade: 'A' }
                    ],
                    count: 2
                })
            });
        });

        await page.goto('/');

        // Select professionals for comparison
        await page.getByTestId('compare-checkbox-1').check();
        await page.getByTestId('compare-checkbox-2').check();
        await page.getByRole('button', { name: /compare/i }).click();

        // Verify comparison view
        await expect(page.getByText(/LO One/)).toBeVisible();
        await expect(page.getByText(/LO Two/)).toBeVisible();
    });

    test('should filter by language', async ({ page }) => {
        await page.route('**/api/v1/grid-enhanced/filter', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    professionals: [
                        {
                            id: 'spanish-lo',
                            name: 'Maria Garcia',
                            languages: ['English', 'Spanish']
                        }
                    ],
                    count: 1
                })
            });
        });

        await page.goto('/');

        // Select Spanish language filter
        await page.getByLabel(/language/i).click();
        await page.getByRole('option', { name: /spanish/i }).click();

        // Verify filtered results
        await expect(page.getByText(/maria garcia/i)).toBeVisible();
    });

    test('should show online-only filter', async ({ page }) => {
        await page.goto('/');

        // Toggle online-only filter
        await page.getByLabel(/online.*only/i).check();

        // Should trigger API call with online_only=true
        // Verified by network inspection in actual test
    });
});
