import { test, expect } from '@playwright/test';
import { setupAllMocks } from './fixtures/api-mocks';

/**
 * E2E Tests for Get Matched Flow
 * 
 * Tests the borrower intake form and matching results display.
 * Form steps: 1) State, 2) Loan Purpose, 3) Property/Timeline, 4) Special Needs
 */

test.describe('Get Matched Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupAllMocks(page);
    });

    test('should display the intake form on /get-matched', async ({ page }) => {
        await page.goto('/get-matched');

        // Check page heading
        await expect(page.getByRole('heading', { name: /find.*loan officer/i })).toBeVisible();

        // Check trust indicators
        await expect(page.getByText(/NMLS verified/i)).toBeVisible();
    });

    test('should show location step first', async ({ page }) => {
        await page.goto('/get-matched');

        // First step asks about location
        await expect(page.getByText(/where.*buying/i)).toBeVisible();

        // Should have state dropdown
        await expect(page.getByRole('combobox')).toBeVisible();
    });

    test('should navigate through multi-step form', async ({ page }) => {
        await page.goto('/get-matched');

        // Step 1: Select state
        await page.getByRole('combobox').selectOption('CA');
        await page.getByRole('button', { name: /continue/i }).click();

        // Step 2: Loan purpose should appear
        await expect(page.getByText(/what.*looking to do/i)).toBeVisible();
        await page.getByRole('button', { name: /purchase/i }).click();
        await page.getByRole('button', { name: /continue/i }).click();

        // Step 3: Property details
        await expect(page.getByText(/tell us more/i)).toBeVisible();
    });

    test('should show matching results after completing form', async ({ page }) => {
        // Mock the matching API response
        await page.route('**/api/v1/matching/**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    borrower_profile: {},
                    matches: [
                        {
                            lo_id: 'test-lo-1',
                            lo_name: 'John Smith',
                            company_name: 'ABC Mortgage',
                            match_score: 92,
                            availability: 'online_now',
                            nmls_verified: true,
                            nmls_id: '123456',
                            avg_rating: 4.8,
                            total_reviews: 50,
                            match_reasons: [
                                { category: 'specialty', reason: 'Specializes in first-time buyers', weight: 0.2, verified: true }
                            ],
                            specialty_names: ['FHA', 'First-Time Buyer'],
                            language_codes: ['en'],
                            has_video: false
                        }
                    ],
                    total_eligible: 10,
                    algorithm_version: '2.0.0',
                    computed_at: new Date().toISOString(),
                    input_hash: 'abc123'
                })
            });
        });

        await page.goto('/get-matched');

        // Complete form
        await page.getByRole('combobox').selectOption('CA');
        await page.getByRole('button', { name: /continue/i }).click();

        await page.getByRole('button', { name: /purchase/i }).click();
        await page.getByRole('button', { name: /continue/i }).click();

        // Step 3: Select timeline
        await page.getByRole('button', { name: /within.*week|immediate/i }).first().click();
        await page.getByRole('button', { name: /continue/i }).click();

        // Step 4: Submit (skip special needs)
        await page.getByRole('button', { name: /find.*loan officer/i }).click();

        // Wait for results
        await expect(page.getByText(/John Smith/i)).toBeVisible({ timeout: 10000 });
        await expect(page.getByText(/92/)).toBeVisible(); // Match score
    });

    test('should display match reasons by default', async ({ page }) => {
        await page.route('**/api/v1/matching/**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    borrower_profile: {},
                    matches: [{
                        lo_id: 'test-lo-1',
                        lo_name: 'Test LO',
                        match_score: 95,
                        nmls_verified: true,
                        avg_rating: 4.5,
                        total_reviews: 30,
                        match_reasons: [
                            { category: 'rating', reason: 'Highly rated professional', weight: 0.2, verified: true },
                            { category: 'availability', reason: 'Available now for instant connection', weight: 0.25, verified: true }
                        ],
                        specialty_names: [],
                        language_codes: ['en'],
                        availability: 'online_now'
                    }],
                    total_eligible: 1,
                    algorithm_version: '2.0.0'
                })
            });
        });

        await page.goto('/get-matched');

        // Quick form completion
        await page.getByRole('combobox').selectOption('TX');
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /purchase/i }).click();
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /immediate|within/i }).first().click();
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /find.*loan/i }).click();

        // Reasons should be visible by default (no click needed)
        await expect(page.getByText(/highly rated/i)).toBeVisible({ timeout: 10000 });
        await expect(page.getByText(/available now/i)).toBeVisible();
    });

    test('should display NMLS verification badge', async ({ page }) => {
        await page.route('**/api/v1/matching/**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    borrower_profile: {},
                    matches: [{
                        lo_id: 'test-lo-1',
                        lo_name: 'Jane Doe',
                        nmls_verified: true,
                        nmls_id: '123456',
                        match_score: 88,
                        avg_rating: 4.7,
                        total_reviews: 45,
                        availability: 'online_now',
                        match_reasons: [],
                        specialty_names: [],
                        language_codes: ['en']
                    }],
                    total_eligible: 1
                })
            });
        });

        await page.goto('/get-matched');

        // Quick completion
        await page.getByRole('combobox').selectOption('NY');
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /refinance/i }).click();
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /immediate|soon|exploring/i }).first().click();
        await page.getByRole('button', { name: /continue/i }).click();
        await page.getByRole('button', { name: /find/i }).click();

        // Check for NMLS badge
        await expect(page.getByText(/NMLS Verified/i)).toBeVisible({ timeout: 10000 });
    });
});
