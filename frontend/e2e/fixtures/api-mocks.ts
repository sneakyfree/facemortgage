import { Page, Route } from '@playwright/test';

/**
 * API mocking helpers for E2E tests.
 * Use these to mock API responses for consistent test behavior.
 */

/**
 * Mock professional grid data.
 */
export const mockProfessionals = [
  {
    id: 'mock-prof-1',
    first_name: 'John',
    last_name: 'Smith',
    user_type: 'loan_officer',
    company_name: 'ABC Mortgage',
    avatar_url: null,
    status: 'online_available',
    video_type: 'live',
    avg_rating: 4.8,
    total_reviews: 125,
    avg_pickup_time_seconds: 15,
    years_experience: 10,
    specialty_names: ['FHA', 'VA', 'Conventional'],
    language_codes: ['en', 'es'],
    nmls_id: '123456',
    grid_position: 1,
  },
  {
    id: 'mock-prof-2',
    first_name: 'Jane',
    last_name: 'Doe',
    user_type: 'realtor',
    company_name: 'XYZ Realty',
    avatar_url: null,
    status: 'online_busy',
    video_type: 'recorded',
    avg_rating: 4.5,
    total_reviews: 89,
    avg_pickup_time_seconds: 22,
    years_experience: 7,
    specialty_names: ['First-time buyers', 'Luxury'],
    language_codes: ['en'],
    nmls_id: null,
    grid_position: 2,
  },
];

/**
 * Mock the professionals grid API response.
 */
export async function mockProfessionalsAPI(page: Page): Promise<void> {
  await page.route('**/api/v1/grid**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        professionals: mockProfessionals,
        total: mockProfessionals.length,
        page: 1,
        page_size: 20,
      }),
    });
  });
}

/**
 * Mock authentication API responses.
 */
export async function mockAuthAPI(page: Page, options?: { authenticated?: boolean }): Promise<void> {
  const isAuthenticated = options?.authenticated ?? false;

  await page.route('**/api/v1/auth/me', async (route: Route) => {
    if (isAuthenticated) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'mock-user-1',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          user_type: 'borrower',
        }),
      });
    } else {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authenticated' }),
      });
    }
  });
}

/**
 * Mock lead capture API.
 */
export async function mockLeadCaptureAPI(page: Page): Promise<void> {
  await page.route('**/api/v1/calls/*/lead', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true }),
    });
  });
}

/**
 * Mock scheduled calls API.
 */
export async function mockScheduledCallsAPI(page: Page): Promise<void> {
  await page.route('**/api/v1/scheduled-calls', async (route: Route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'mock-scheduled-1',
          scheduled_for: new Date().toISOString(),
          status: 'scheduled',
        }),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ scheduled_calls: [] }),
      });
    }
  });
}

/**
 * Mock billing/subscription API.
 */
export async function mockBillingAPI(page: Page): Promise<void> {
  await page.route('**/api/v1/billing/subscription', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        subscription: {
          tier: 'professional',
          status: 'active',
          current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
      }),
    });
  });

  await page.route('**/api/v1/billing/checkout', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        checkout_url: 'https://checkout.stripe.com/mock-session',
      }),
    });
  });
}

/**
 * Mock data provider stats API (baseball card).
 */
export async function mockStatsAPI(page: Page): Promise<void> {
  await page.route('**/api/v1/data/stats/*', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        nmls_id: '123456',
        total_loans: 450,
        avg_loan_amount: 325000,
        top_loan_types: ['Conventional', 'FHA', 'VA'],
        state_breakdown: {
          CA: 200,
          TX: 150,
          FL: 100,
        },
        last_updated: new Date().toISOString(),
      }),
    });
  });
}

/**
 * Setup all common mocks for testing.
 */
export async function setupAllMocks(page: Page): Promise<void> {
  await mockProfessionalsAPI(page);
  await mockAuthAPI(page, { authenticated: false });
  await mockLeadCaptureAPI(page);
  await mockScheduledCallsAPI(page);
}
