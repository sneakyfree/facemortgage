# FaceMortgage Frontend

A Next.js 16 application for connecting borrowers with mortgage professionals through real-time video calls.

## Tech Stack

- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **Styling:** Tailwind CSS 4
- **Testing:** Vitest + React Testing Library + Playwright
- **Video Calls:** WebRTC / LiveKit

## Prerequisites

- Node.js 20+
- npm 10+
- Backend API running on `http://localhost:8000`

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env.local
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open [http://localhost:3000](http://localhost:3000)**

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for real-time features | `ws://localhost:8000` |
| `NEXT_PUBLIC_VAPID_PUBLIC_KEY` | VAPID key for push notifications | - |
| `NEXT_PUBLIC_LIVEKIT_URL` | LiveKit server URL (if using LiveKit) | - |

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (marketing)/        # Public marketing pages
│   │   ├── page.tsx        # Homepage with professional grid
│   │   ├── how-it-works/   # How it works page
│   │   ├── for-professionals/  # Professional signup page
│   │   ├── terms/          # Terms of service
│   │   └── privacy/        # Privacy policy
│   ├── auth/               # Authentication pages
│   │   ├── login/          # Login page
│   │   ├── register/       # Registration page
│   │   └── forgot-password/ # Password reset
│   ├── dashboard/          # Protected professional dashboard
│   │   ├── page.tsx        # Dashboard home with stats
│   │   ├── settings/       # Profile and settings
│   │   ├── analytics/      # Analytics and metrics
│   │   ├── leads/          # Lead management
│   │   ├── partnerships/   # Partnership management
│   │   └── billing/        # Subscription billing
│   ├── admin/              # Admin dashboard
│   ├── partner/            # Partner portal
│   ├── embed/              # Embeddable widgets
│   │   ├── widget/         # Embeddable video grid
│   │   └── get-matched/    # Lead capture form
│   └── checkout/           # Stripe checkout flow
├── components/
│   ├── call/               # Video call components
│   │   ├── VideoCall.tsx   # Main video call UI
│   │   ├── RingingModal.tsx # Incoming call modal
│   │   ├── LeadCaptureModal.tsx # Anonymous caller info
│   │   └── ScheduleCallModal.tsx # Schedule future call
│   ├── filters/            # Filter components
│   │   └── FilterPanel.tsx # Professional filtering UI
│   ├── forms/              # Form components
│   │   └── GetMatchedForm.tsx # Lead matching form
│   ├── geo/                # Geolocation components
│   │   └── GeoPrompt.tsx   # Location permission prompt
│   ├── grid/               # Professional grid components
│   │   ├── ProfessionalGrid.tsx # Main grid display
│   │   └── BaseballCard/   # Professional profile card
│   ├── layout/             # Layout components
│   │   ├── Header.tsx      # Site header/navigation
│   │   └── Footer.tsx      # Site footer
│   ├── partnership/        # Partnership components
│   │   ├── ReferralModal.tsx # Send referral modal
│   │   └── InvitePartnerModal.tsx # Invite partner modal
│   └── ui/                 # Reusable UI primitives
│       ├── Button.tsx
│       ├── Modal.tsx
│       └── ...
├── hooks/                  # Custom React hooks
│   ├── useFocusTrap.ts     # Accessibility focus trap
│   ├── useGeoLocation.ts   # Browser geolocation
│   ├── useProfessionalPresence.ts # WebSocket presence
│   ├── usePushNotifications.ts # Push notification subscription
│   ├── useRealtimeGrid.ts  # Real-time grid updates
│   └── useVideoCall.ts     # WebRTC video call management
├── lib/                    # Utilities and configuration
│   ├── api/
│   │   └── client.ts       # Axios API client with auth
│   ├── config.ts           # App configuration
│   └── utils.ts            # Helper functions
├── stores/                 # Zustand state stores
│   ├── authStore.ts        # Authentication state
│   ├── filterStore.ts      # Filter state
│   └── gridStore.ts        # Grid display state
└── types/                  # TypeScript type definitions
    └── index.ts            # Shared types
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm test` | Run unit tests (Vitest) |
| `npm run test:ui` | Run tests with Vitest UI |
| `npm run test:coverage` | Run tests with coverage |
| `npm run test:e2e` | Run Playwright E2E tests |
| `npm run test:e2e:ui` | Run E2E tests with Playwright UI |
| `npm run test:e2e:headed` | Run E2E tests in headed browser |

## Key Features

### Professional Grid
Real-time grid of available mortgage professionals with filtering by:
- State/location
- Professional type (Loan Officer, Realtor, Title Rep, Attorney)
- Language
- Specialty
- Rating

### Video Calls
- WebRTC-based video calls (or LiveKit for scalable deployment)
- Anonymous calling with lead capture
- Call scheduling
- Real-time presence indicators

### Authentication
- JWT-based authentication with httpOnly cookies
- OAuth support (Google, etc.)
- CSRF protection
- Secure session management

### Dashboard
Professional dashboard with:
- Call statistics and analytics
- Lead management
- Partnership/referral system
- Subscription billing (Stripe)
- Profile settings

## Authentication Flow

The app uses httpOnly cookies for secure token storage:

1. User logs in via `/auth/login`
2. Backend sets `access_token` and `refresh_token` cookies
3. All API requests include cookies automatically
4. CSRF token is included in state-changing requests
5. Token refresh happens automatically on 401 responses

## Testing

### Unit Tests (Vitest)

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/hooks/useVideoCall.test.ts
```

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific test
npm run test:e2e -- tests/auth.spec.ts
```

## Development Notes

### Logging
Use the `logger` utility from `@/lib/utils` instead of `console.log`:

```typescript
import { logger } from '@/lib/utils';

logger.log('Debug message');   // Only in development
logger.warn('Warning');        // Only in development
logger.error('Error');         // Always logged
logger.debug('Debug');         // Only in development, with [DEBUG] prefix
```

### API Client
Use the pre-configured axios client for API calls:

```typescript
import { apiClient } from '@/lib/api/client';

// GET request
const { data } = await apiClient.get('/professionals');

// POST request
await apiClient.post('/leads', { name, email });
```

### State Management
- **Zustand** for global state (auth, filters, grid)
- **TanStack Query** for server state and caching

```typescript
// Zustand store
const { user, isAuthenticated } = useAuthStore();

// TanStack Query
const { data, isLoading } = useQuery({
  queryKey: ['professionals'],
  queryFn: () => apiClient.get('/professionals'),
});
```

## Deployment

### Build
```bash
npm run build
```

### Environment Variables for Production
Ensure all `NEXT_PUBLIC_*` variables are set in your deployment environment:

```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-vapid-public-key
```

## License

Proprietary - All rights reserved.
