# FaceMortgage Comprehensive Gap Analysis
**Date:** January 2025
**Scope:** Security, Testing, Accessibility, Code Quality, Documentation

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Backend Security | 2 | 5 | 6 | 5 | 18 |
| Frontend Security | 0 | 0 | 4 | 2 | 6 |
| Accessibility (WCAG 2.1 AA) | 0 | 4 | 8 | 3 | 15 |
| Test Coverage | 3 | 8 | 10 | 4 | 25 |
| Code Quality | 0 | 1 | 4 | 3 | 8 |
| Documentation | 0 | 0 | 4 | 2 | 6 |
| **TOTAL** | **5** | **18** | **36** | **19** | **78** |

**Current Test Coverage:** ~40% overall (30% backend, 60% frontend)
**Target Test Coverage:** 75%

---

## 1. BACKEND SECURITY GAPS

### CRITICAL (Immediate Action Required)

#### 1.1 Stripe Webhook Signature Verification Error Exposure
**File:** `backend/src/app/api/v1/routes/billing.py:459-462`
```python
except (stripe.error.SignatureVerificationError, ValueError) as e:
    raise HTTPException(status_code=400, detail=str(e))
```
**Risk:** Exception message exposed to client, leaking signature verification details.
**Fix:** Return generic error message: `"Invalid webhook signature"`

#### 1.2 Missing NMLS ID Validation Before External API Calls
**File:** `backend/src/app/api/v1/routes/professionals.py:548-560`
**Risk:** NMLS ID passed directly to external providers without format validation. Could enable injection if providers construct URLs/queries with this value.
**Fix:** Validate NMLS ID format (numeric, 6-12 digits) before external calls.

### HIGH

| ID | Issue | File | Line |
|----|-------|------|------|
| 1.3 | WebSocket professional_id enumeration | `main.py` | 314-361 |
| 1.4 | Cookie secure=false risk in dev | `config.py` | 39-41 |
| 1.5 | Weak password policy (length only) | `users.py` | 78-82 |
| 1.6 | Missing rate limit on soft lead endpoint | `soft_leads.py` | 73-129 |
| 1.7 | Avatar upload path traversal risk | `users.py` | 174-178 |

### MEDIUM

| ID | Issue | File | Line |
|----|-------|------|------|
| 1.8 | CORS allows localhost in production | `config.py` | 72-80 |
| 1.9 | CSP allows unsafe-inline/unsafe-eval | `main.py` | 41-49 |
| 1.10 | Admin role check uses getattr default | `admin.py` | 26-31 |
| 1.11 | Exception exposes internal errors | `professionals.py` | 594-596 |
| 1.12 | Anonymous users can schedule calls | `scheduled_calls.py` | 66-171 |
| 1.13 | Missing file magic byte validation | `users.py` | 156-161 |

### LOW

| ID | Issue | File |
|----|-------|------|
| 1.14 | Database URL with default credentials | `config.py:24` |
| 1.15 | JWT uses HS256 (consider RS256) | `config.py:34` |
| 1.16 | Missing account lockout mechanism | `auth.py` |
| 1.17 | WebSocket grid endpoint no auth | `main.py:364-376` |
| 1.18 | Sensitive headers may leak to external APIs | Data providers |

---

## 2. FRONTEND SECURITY GAPS

### MEDIUM

| ID | Issue | File | Line |
|----|-------|------|------|
| 2.1 | Missing CSRF token protection | All API calls | - |
| 2.2 | localStorage token check inconsistency | `useVideoCall.ts` | 286-287 |
| 2.3 | Client-side only password validation | `register/page.tsx` | 47-56 |
| 2.4 | Client-side only form validation | `GetMatchedForm.tsx` | - |

### LOW

| ID | Issue | File |
|----|-------|------|
| 2.5 | User ID stored in localStorage | `authStore.ts:28` |
| 2.6 | Session ID in sessionStorage | `ProfessionalGrid.tsx:16-19` |

---

## 3. ACCESSIBILITY GAPS (WCAG 2.1 AA)

### HIGH (Blocks WCAG Compliance)

| ID | Issue | Files Affected |
|----|-------|----------------|
| 3.1 | Non-functional skip link (missing #main-content target) | `layout.tsx`, `Header.tsx` |
| 3.2 | Missing form label associations (htmlFor/id) | 8+ files: LeadCaptureModal, ScheduleCallModal, GetMatchedForm, FilterPanel, settings/page, ReferralModal, InvitePartnerModal |
| 3.3 | Missing role="alert" on error messages | `login/page.tsx`, `register/page.tsx`, `GetMatchedForm.tsx`, `settings/page.tsx` |
| 3.4 | Missing focus trap in BaseballCard modal | `BaseballCard.tsx` |

### MEDIUM

| ID | Issue | Files |
|----|-------|-------|
| 3.5 | Missing aria-labels on icon buttons | `BaseballCard.tsx`, `FilterPanel.tsx` |
| 3.6 | Tab navigation lacks ARIA attributes | `settings/page.tsx` |
| 3.7 | Potential color contrast issues | Multiple files using `text-gray-400/500` |
| 3.8 | Missing landmark footer | `layout.tsx` |
| 3.9-3.16 | Various minor ARIA improvements | Multiple components |

### LOW

| ID | Issue | Files |
|----|-------|-------|
| 3.17 | Generic alt text "Avatar" | `settings/page.tsx:304` |
| 3.18 | LiveRegion underutilized | Application-wide |
| 3.19 | Missing aria-describedby for complex forms | Multiple |

---

## 4. TEST COVERAGE GAPS

### CRITICAL (Security-Related)

| ID | Module | Current Coverage | Target |
|----|--------|-----------------|--------|
| 4.1 | `core/security.py` (JWT, password hashing) | 0% | 95% |
| 4.2 | `middleware/csrf.py` (CSRF protection) | 0% | 95% |
| 4.3 | `integrations/stripe/service.py` (Payments) | 0% | 90% |

### HIGH

| ID | Module | Current Coverage | Target |
|----|--------|-----------------|--------|
| 4.4 | `core/dependencies.py` (Auth dependencies) | ~20% | 90% |
| 4.5 | `core/validators.py` (Input validation) | 0% | 85% |
| 4.6 | `core/rate_limit.py` | 0% | 80% |
| 4.7 | `services/email_service.py` | 0% | 75% |
| 4.8 | `services/push_notification.py` | 0% | 75% |
| 4.9 | `signaling/*.py` (WebRTC signaling) | 0% | 80% |
| 4.10 | `grid/ranking.py` (Ranking algorithm) | 0% | 85% |
| 4.11 | `api/v1/routes/videos.py` | 0% | 75% |

### MEDIUM

| ID | Module | Current Coverage | Target |
|----|--------|-----------------|--------|
| 4.12 | `services/video_service.py` | 0% | 70% |
| 4.13 | `integrations/livekit/service.py` | 0% | 70% |
| 4.14 | `grid/service.py` | 0% | 70% |
| 4.15 | Data provider implementations | ~30% | 70% |
| 4.16 | `workers/tasks.py` (Celery tasks) | 0% | 65% |
| 4.17 | `services/storage.py` | 0% | 65% |
| 4.18 | `hooks/useFocusTrap.ts` | Has tests | Review |
| 4.19 | `hooks/usePushNotifications.ts` | 0% | 80% |

### Frontend Test Gaps

| ID | Component/Hook | Status | Priority |
|----|----------------|--------|----------|
| 4.20 | `useVideoCall.ts` | ~65% coverage | HIGH - missing WebSocket reconnection tests |
| 4.21 | `authStore.ts` | ~85% coverage | MEDIUM - missing race condition tests |
| 4.22 | `useProfessionalPresence.ts` | ~80% coverage | MEDIUM - missing tab visibility tests |
| 4.23 | Model tests (all 12 model files) | 0% | MEDIUM |

---

## 5. CODE QUALITY GAPS

### HIGH

| ID | Issue | Details |
|----|-------|---------|
| 5.1 | Duplicate code in data providers | 4 files with 80%+ similarity: datagod.py, modex.py, corelogic.py, redr.py |

### MEDIUM

| ID | Issue | Locations |
|----|-------|-----------|
| 5.2 | Overly broad exception handling | 7 instances across database.py, storage.py, lookups.py, health.py, dependencies.py |
| 5.3 | Hardcoded configuration values | 15+ values that should be in settings (timeouts, URLs, limits) |
| 5.4 | Long/complex route handlers | `calls.py:initiate_call()` - 203 lines |
| 5.5 | Console.log statements in production | 45+ statements across frontend hooks |

### LOW

| ID | Issue | Details |
|----|-------|---------|
| 5.6 | Missing `-> None` on `__init__` methods | Multiple data provider classes |
| 5.7 | Inconsistent DbSession vs AsyncSession usage | Route files |
| 5.8 | Inconsistent docstring coverage | Some routes documented, others not |

---

## 6. DOCUMENTATION GAPS

### MEDIUM

| ID | Issue | Location |
|----|-------|----------|
| 6.1 | Frontend README is Next.js boilerplate | `frontend/README.md` |
| 6.2 | Missing architecture documentation | WebSocket flows, data providers, ranking algorithm |
| 6.3 | Missing API usage guide | Beyond OpenAPI auto-docs |
| 6.4 | Incomplete OpenAPI descriptions | `auth.py`, `calls.py`, `grid.py` missing response_models |

### LOW

| ID | Issue | Location |
|----|-------|----------|
| 6.5 | Missing docstrings | `auth.py` route handlers, helper functions |
| 6.6 | No inline code documentation for complex algorithms | `grid/ranking.py` |

---

## 7. PRIORITIZED REMEDIATION PLAN

### Phase 1: Critical Security (Immediate)
1. Fix webhook error message exposure (1.1)
2. Add NMLS ID validation (1.2)
3. Implement CSRF token handling in frontend (2.1)
4. Add tests for security.py, csrf.py, stripe/service.py (4.1-4.3)

### Phase 2: High Priority Security & Accessibility (Week 1)
1. Strengthen password policy (1.5)
2. Add file magic byte validation (1.13)
3. Fix skip link target (3.1)
4. Add form label associations (3.2)
5. Add role="alert" to error messages (3.3)
6. Add focus trap to BaseballCard (3.4)

### Phase 3: Test Coverage Expansion (Weeks 2-3)
1. Auth dependencies tests (4.4)
2. Input validation tests (4.5)
3. Rate limiting tests (4.6)
4. Email/push notification service tests (4.7-4.8)
5. WebRTC signaling tests (4.9)
6. Ranking algorithm tests (4.10)

### Phase 4: Code Quality (Week 4)
1. Refactor data provider duplication (5.1)
2. Replace bare except clauses (5.2)
3. Move hardcoded values to config (5.3)
4. Replace console.log with structured logging (5.5)

### Phase 5: Documentation (Ongoing)
1. Update frontend README (6.1)
2. Create architecture documentation (6.2)
3. Complete OpenAPI descriptions (6.4)
4. Add missing docstrings (6.5)

---

## 8. SUCCESS METRICS

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Critical security issues | 2 | 0 | Week 1 |
| High security issues | 5 | 0 | Week 2 |
| Backend test coverage | ~30% | 75% | Week 4 |
| Frontend test coverage | ~60% | 80% | Week 3 |
| WCAG 2.1 AA compliance | ~70% | 95% | Week 2 |
| API endpoints documented | ~60% | 100% | Week 4 |

---

## Appendix: Files Requiring Immediate Attention

### Backend
1. `backend/src/app/api/v1/routes/billing.py` - Webhook error exposure
2. `backend/src/app/api/v1/routes/professionals.py` - NMLS validation, error exposure
3. `backend/src/app/api/v1/routes/users.py` - Password policy, file validation
4. `backend/src/app/core/security.py` - Needs tests
5. `backend/src/app/middleware/csrf.py` - Needs tests

### Frontend
1. `frontend/src/app/layout.tsx` - Add id="main-content" to main element
2. `frontend/src/components/call/LeadCaptureModal.tsx` - Form label associations
3. `frontend/src/components/call/ScheduleCallModal.tsx` - Form label associations
4. `frontend/src/components/forms/GetMatchedForm.tsx` - Form label associations, role="alert"
5. `frontend/src/components/grid/BaseballCard/BaseballCard.tsx` - Focus trap, aria-label
6. `frontend/src/app/auth/login/page.tsx` - role="alert" on errors
7. `frontend/src/app/auth/register/page.tsx` - role="alert" on errors
