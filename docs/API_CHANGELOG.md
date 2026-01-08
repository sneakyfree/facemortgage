# FaceMortgage API Changelog

All notable changes to the FaceMortgage API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-01-06

### Initial Release

The first production-ready release of the FaceMortgage API.

#### Added

**Authentication (`/api/v1/auth`)**
- `POST /register` - User registration with role selection
- `POST /login` - Authentication with JWT tokens
- `POST /logout` - Session termination
- `POST /refresh` - Token refresh
- `GET /me` - Current user profile
- `POST /verify-email` - Email verification
- `POST /request-password-reset` - Password reset initiation
- `POST /reset-password` - Password reset completion

**Professional Grid (`/api/v1/grid`)**
- `GET /` - Paginated professional listing with filters
- `GET /lookup-data` - Filter options (states, specialties, languages)
- `POST /impression` - Track professional card impressions
- `POST /click` - Track professional card clicks

**Professionals (`/api/v1/professionals`)**
- `GET /{id}` - Public professional profile
- `GET /me` - Current professional's profile
- `PUT /me` - Update professional profile
- `GET /me/dashboard` - Professional dashboard stats
- `POST /me/status` - Update availability status

**Video Calls (`/api/v1/calls`)**
- `POST /initiate` - Start a call with a professional
- `GET /{call_id}` - Get call details
- `POST /{call_id}/rate` - Rate a completed call
- `POST /{call_id}/lead` - Submit lead capture form

**Scheduled Calls (`/api/v1/scheduled-calls`)**
- `POST /` - Schedule a call for later
- `GET /` - List scheduled calls
- `GET /{id}` - Get scheduled call details
- `DELETE /{id}` - Cancel scheduled call

**Billing (`/api/v1/billing`)**
- `GET /subscription` - Current subscription status
- `POST /checkout` - Create Stripe checkout session
- `POST /portal` - Create Stripe billing portal session
- `POST /webhook` - Stripe webhook handler

**Data Providers (`/api/v1/data`)**
- `GET /stats/{nmls_id}` - Professional statistics from data providers

**Partnerships (`/api/v1/partnerships`)**
- `GET /referral-stats` - Referral program statistics
- `POST /referral` - Create referral link
- `POST /partner-request` - Request partnership

**Health (`/health`)**
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe with dependency checks

#### WebSocket Endpoints
- `ws://host/ws/presence/{professional_id}` - Professional online status
- `ws://host/ws/grid` - Real-time grid updates
- `ws://host/ws/signaling/{room_id}/{user_id}` - WebRTC signaling

#### Security Features
- JWT authentication with httpOnly cookie storage
- Rate limiting on all endpoints
- CORS configuration
- Security headers (HSTS, CSP, X-Frame-Options)
- Request ID tracking for distributed tracing

---

## Migration Guides

### Migrating from Beta to 1.0.0

If you were using the beta API, note these changes:

1. **Authentication**: Tokens are now stored in httpOnly cookies for browser clients. API clients should continue using the Authorization header.

2. **WebSocket Authentication**: Query parameter tokens are no longer supported. Use:
   - Cookies (automatic for browsers)
   - `Sec-WebSocket-Protocol: auth, <token>` header

3. **Rate Limits**: Rate limiting is now enforced. Check response headers for limit status.

4. **Error Format**: All errors now include an `error_code` field for programmatic handling.

---

## Deprecation Policy

- Features marked as deprecated will be supported for at least 6 months
- Deprecated features will be clearly marked in the API documentation
- Breaking changes will only be introduced in major version releases

---

## Versioning

The API uses URL path versioning (`/api/v1/...`). When a new major version is released:

1. The new version will be available at `/api/v2/...`
2. The old version will continue to work during the deprecation period
3. Migration guides will be provided for breaking changes

---

## Rate Limit Reference

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Authentication | 5 | 1 minute |
| Grid (read) | 100 | 1 minute |
| Profile (read) | 100 | 1 minute |
| Profile (write) | 30 | 1 minute |
| Calls | 20 | 1 minute |
| Billing | 10 | 1 minute |
| Data providers | 30 | 1 minute |

---

## Support

For API questions or to report issues:
- Email: support@facemortgage.com
- Documentation: https://api.facemortgage.com/api/v1/docs
