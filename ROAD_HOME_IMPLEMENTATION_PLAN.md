# ROAD HOME IMPLEMENTATION PLAN

## FaceMortgage Platform - Complete Gap Remediation & 10/10 UX Achievement

**Document Version:** 1.0
**Created:** January 2025
**Target Completion:** All gaps closed, all features at 10/10 UX

---

## STRATEGY SUMMARY

This plan closes 47 identified gaps across 10 categories to achieve production readiness. Priority order: (1) Fix broken/missing critical features blocking launch (UX 0-4), (2) Complete partial implementations causing user friction (UX 5-6), (3) Polish working features to excellence (UX 7-9). Each task is atomic, explicit, and testable. Frontend and backend work in parallel where possible. All changes require tests, accessibility compliance, and error handling. No task is complete until it passes Definition of Done. Estimated scope: 6 phases over 8-10 weeks. Quality gates at each phase prevent regression.

---

## DEFINITION OF DONE (10/10 UX Standard)

Every feature must satisfy ALL criteria before marking complete:

### Functional Completeness
- [ ] All acceptance criteria pass
- [ ] Feature works in Chrome, Firefox, Safari, Edge (latest 2 versions)
- [ ] Feature works on mobile viewport (375px) and desktop (1440px)
- [ ] No console errors or warnings
- [ ] No network errors in happy path

### User Experience
- [ ] Loading states shown for all async operations (spinner/skeleton within 100ms)
- [ ] Error states have clear message + actionable recovery option
- [ ] Empty states have helpful illustration + call-to-action
- [ ] Success states have confirmation feedback (toast/inline message)
- [ ] Form validation shows inline errors on blur, not just on submit
- [ ] All copy is clear, concise, and action-oriented

### Accessibility
- [ ] Keyboard navigation works (Tab, Shift+Tab, Enter, Escape)
- [ ] Focus visible on all interactive elements
- [ ] ARIA labels on all icon-only buttons
- [ ] Form inputs have associated labels (htmlFor + id)
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Screen reader announces dynamic content changes (role="alert")

### Performance
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] No layout shifts after initial paint
- [ ] Images lazy-loaded below fold
- [ ] API responses < 500ms for reads, < 2s for writes

### Reliability
- [ ] Handles network failures gracefully (retry + offline message)
- [ ] Handles API errors gracefully (user-friendly message, no stack traces)
- [ ] Handles edge cases (empty data, null values, very long strings)
- [ ] No data loss on browser refresh during forms
- [ ] Idempotent operations where applicable

### Testing
- [ ] Unit tests for business logic (>80% coverage for new code)
- [ ] Integration tests for API endpoints
- [ ] E2E test for critical user path
- [ ] Manual QA verification documented

### Observability
- [ ] Errors logged with context (user ID, action, timestamp)
- [ ] Key metrics tracked (latency, error rate, usage count)
- [ ] Analytics events for user actions

---

## PRIORITIZATION TIERS

### Tier 1: FIX FIRST (Blockers - UX 0-4)
Must complete before any public launch. These are broken, missing, or unusable.

| Feature | Current UX | Target UX | Phase |
|---------|-----------|-----------|-------|
| Content Moderation | 0 | 10 | 1 |
| Dispute Resolution | 0 | 10 | 1 |
| Pre-recorded Video Upload UI | 2 | 10 | 1 |
| Email Verification UI | 2 | 10 | 1 |
| User Management Admin | 2 | 10 | 1 |
| Privacy Policy Content | 3 | 10 | 1 |
| Terms of Service Content | 3 | 10 | 1 |
| Audit Logs Viewer | 3 | 10 | 1 |
| Comparative Benchmarks | 3 | 10 | 2 |
| Push Notifications | 4 | 10 | 2 |
| Admin Dashboard | 4 | 10 | 2 |

### Tier 2: HIGH IMPACT (Friction - UX 5-6)
Complete within first month post-launch. Users can work around these but experience friction.

| Feature | Current UX | Target UX | Phase |
|---------|-----------|-----------|-------|
| OAuth Completion | 5 | 10 | 3 |
| Call Quality Metrics | 5 | 10 | 3 |
| Missed Call Notifications | 5 | 10 | 3 |
| Lead Export UI | 5 | 10 | 3 |
| Notification Preferences UI | 5 | 10 | 3 |
| Commission Tracking UI | 5 | 10 | 3 |
| System Health Dashboard | 5 | 10 | 3 |
| Account Deletion UX | 5 | 10 | 3 |
| Call Recording Playback | 6 | 10 | 4 |
| Usage-based Billing Display | 6 | 10 | 4 |
| Email Notification Tracking | 6 | 10 | 4 |

### Tier 3: POLISH (Excellence - UX 7-9)
Continuous improvement. Features work but can be refined.

| Feature | Current UX | Target UX | Phase |
|---------|-----------|-----------|-------|
| Password Reset Flow | 7 | 10 | 5 |
| User Profile Management | 7 | 10 | 5 |
| Video Preview on Hover | 7 | 10 | 5 |
| Schedule Call Feature | 7 | 10 | 5 |
| Screen Sharing | 7 | 10 | 5 |
| Lead Assignment | 7 | 10 | 5 |
| Bid Wallet System | 7 | 10 | 5 |
| Promo Codes | 7 | 10 | 5 |
| Revenue Analytics | 7 | 10 | 5 |
| Partnership Analytics | 7 | 10 | 5 |
| In-App Notifications | 7 | 10 | 5 |
| NMLS Verification | 7 | 10 | 5 |
| Cookie Consent | 7 | 10 | 5 |

### Tier 4: NEW FEATURES (Vision Items)
Features from vision document not yet implemented.

| Feature | Current UX | Target UX | Phase |
|---------|-----------|-----------|-------|
| SMS Notifications | 1 | 10 | 4 |
| Lead Import | 0 | 10 | 4 |
| Lead Scoring | 2 | 10 | 4 |
| Export Reports | 2 | 10 | 4 |
| Data Export (GDPR) | 2 | 10 | 4 |

---

## PHASE 1: CRITICAL BLOCKERS

**Duration:** 2 weeks
**Goal:** Close all UX 0-3 gaps that block launch

---

### EPIC 1.1: Content Moderation System

**Goal:** Enable admins to review, approve, or reject professional video content before it appears in the grid.

**Current State:** No moderation capability exists. Videos go live immediately.
**Target State:** All videos queue for review. Admins can approve/reject with one click. Rejected videos show clear reason to professional.

---

#### TASK 1.1.1: Create Video Moderation Data Model

**Goal:** Store moderation status and history for each professional video.

**Scope:**
- INCLUDED: New database table, migration, model class
- EXCLUDED: UI, API endpoints (separate tasks)

**Dependencies:** None

**Prerequisites:**
- Database access configured
- Alembic migrations working

**Implementation Steps:**

1. Create migration file:
```bash
cd backend
alembic revision --autogenerate -m "add_video_moderation_table"
```

2. Edit the generated migration file to create table:
```python
# In the upgrade() function:
op.create_table(
    'video_moderations',
    sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
    sa.Column('professional_id', sa.UUID(), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
    sa.Column('video_url', sa.String(500), nullable=False),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='moderation_status'), nullable=False, default='pending'),
    sa.Column('reviewed_by', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('rejection_reason', sa.String(500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
)
op.create_index('ix_video_moderations_status', 'video_moderations', ['status'])
op.create_index('ix_video_moderations_professional_id', 'video_moderations', ['professional_id'])
```

3. Create SQLAlchemy model in `backend/src/app/models/moderation.py`:
```python
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class ModerationStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class VideoModeration(Base):
    __tablename__ = "video_moderations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    professional_id = Column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False)
    video_url = Column(String(500), nullable=False)
    status = Column(Enum(ModerationStatus), nullable=False, default=ModerationStatus.PENDING)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    professional = relationship("ProfessionalProfile", back_populates="video_moderations")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
```

4. Add relationship to ProfessionalProfile model:
```python
# In backend/src/app/models/professional.py, add:
video_moderations = relationship("VideoModeration", back_populates="professional", order_by="desc(VideoModeration.created_at)")
```

5. Run migration:
```bash
alembic upgrade head
```

**Acceptance Criteria:**
- [ ] Migration runs without errors
- [ ] Table exists with all columns and indexes
- [ ] Model can be imported without errors
- [ ] Can create, read, update VideoModeration records in Python shell

**Testing Requirements:**
- Unit test: Create VideoModeration with all fields
- Unit test: Verify enum values work correctly
- Unit test: Verify foreign key relationships load
- Integration test: Migration up and down works

**Observability:**
- Log migration success/failure

**Risks & Mitigations:**
- Risk: Migration conflicts with existing schema
- Mitigation: Test on fresh database first, backup production before running

---

#### TASK 1.1.2: Create Video Moderation API Endpoints

**Goal:** Provide REST API for video moderation operations.

**Scope:**
- INCLUDED: List pending videos, approve video, reject video, get moderation history
- EXCLUDED: UI components, file upload (handled elsewhere)

**Dependencies:** Task 1.1.1 (data model)

**Prerequisites:**
- VideoModeration model exists
- Admin authentication working

**Implementation Steps:**

1. Create Pydantic schemas in `backend/src/app/schemas/moderation.py`:
```python
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from src.app.models.moderation import ModerationStatus

class VideoModerationBase(BaseModel):
    video_url: str
    status: ModerationStatus

class VideoModerationCreate(BaseModel):
    professional_id: UUID
    video_url: str

class VideoModerationResponse(BaseModel):
    id: UUID
    professional_id: UUID
    video_url: str
    status: ModerationStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested professional info for display
    professional_name: Optional[str] = None
    professional_email: Optional[str] = None

    class Config:
        from_attributes = True

class ApproveVideoRequest(BaseModel):
    """Empty body - approval needs no additional data"""
    pass

class RejectVideoRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500, description="Reason must be 10-500 characters")

class ModerationListResponse(BaseModel):
    items: List[VideoModerationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ModerationStatsResponse(BaseModel):
    pending_count: int
    approved_today: int
    rejected_today: int
    avg_review_time_hours: float
```

2. Create router in `backend/src/app/api/v1/routes/moderation.py`:
```python
"""
Video Moderation API routes for admin content review.
"""
import logging
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Request, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentAdmin
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.moderation import VideoModeration, ModerationStatus
from src.app.models.professional import ProfessionalProfile
from src.app.models.user import User
from src.app.schemas.moderation import (
    VideoModerationResponse,
    ApproveVideoRequest,
    RejectVideoRequest,
    ModerationListResponse,
    ModerationStatsResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pending", response_model=ModerationListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_pending_videos(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all videos pending moderation review.

    Returns paginated list sorted by oldest first (FIFO queue).
    Only accessible by admin users.
    """
    offset = (page - 1) * page_size

    # Count total pending
    count_query = select(func.count(VideoModeration.id)).where(
        VideoModeration.status == ModerationStatus.PENDING
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get pending videos with professional info
    query = (
        select(VideoModeration)
        .options(selectinload(VideoModeration.professional).selectinload(ProfessionalProfile.user))
        .where(VideoModeration.status == ModerationStatus.PENDING)
        .order_by(VideoModeration.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    moderations = result.scalars().all()

    # Build response with professional info
    items = []
    for mod in moderations:
        item = VideoModerationResponse(
            id=mod.id,
            professional_id=mod.professional_id,
            video_url=mod.video_url,
            status=mod.status,
            reviewed_by=mod.reviewed_by,
            reviewed_at=mod.reviewed_at,
            rejection_reason=mod.rejection_reason,
            created_at=mod.created_at,
            updated_at=mod.updated_at,
            professional_name=f"{mod.professional.user.first_name} {mod.professional.user.last_name}" if mod.professional and mod.professional.user else None,
            professional_email=mod.professional.user.email if mod.professional and mod.professional.user else None,
        )
        items.append(item)

    total_pages = (total + page_size - 1) // page_size

    return ModerationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/{moderation_id}/approve", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def approve_video(
    request: Request,
    moderation_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Approve a video for display in the grid.

    Updates moderation status to 'approved' and records reviewer.
    Video becomes visible in grid immediately.
    """
    # Get moderation record
    query = select(VideoModeration).where(VideoModeration.id == moderation_id)
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    if moderation.status != ModerationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video already {moderation.status.value}. Cannot approve.",
        )

    # Update status
    moderation.status = ModerationStatus.APPROVED
    moderation.reviewed_by = current_admin.id
    moderation.reviewed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(moderation)

    logger.info(f"Video {moderation_id} approved by admin {current_admin.id}")

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
    )


@router.post("/{moderation_id}/reject", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def reject_video(
    request: Request,
    moderation_id: UUID,
    body: RejectVideoRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Reject a video with a reason.

    Updates moderation status to 'rejected' and stores reason.
    Professional receives notification with rejection reason.
    """
    # Get moderation record
    query = select(VideoModeration).where(VideoModeration.id == moderation_id)
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    if moderation.status != ModerationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video already {moderation.status.value}. Cannot reject.",
        )

    # Update status
    moderation.status = ModerationStatus.REJECTED
    moderation.reviewed_by = current_admin.id
    moderation.reviewed_at = datetime.utcnow()
    moderation.rejection_reason = body.reason

    await db.commit()
    await db.refresh(moderation)

    logger.info(f"Video {moderation_id} rejected by admin {current_admin.id}: {body.reason}")

    # TODO: Send notification to professional about rejection

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
    )


@router.get("/stats", response_model=ModerationStatsResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_moderation_stats(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Get moderation queue statistics.

    Returns counts for pending, approved today, rejected today,
    and average review time.
    """
    today = date.today()

    # Pending count
    pending_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            VideoModeration.status == ModerationStatus.PENDING
        )
    )
    pending_count = pending_result.scalar() or 0

    # Approved today
    approved_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            and_(
                VideoModeration.status == ModerationStatus.APPROVED,
                func.date(VideoModeration.reviewed_at) == today,
            )
        )
    )
    approved_today = approved_result.scalar() or 0

    # Rejected today
    rejected_result = await db.execute(
        select(func.count(VideoModeration.id)).where(
            and_(
                VideoModeration.status == ModerationStatus.REJECTED,
                func.date(VideoModeration.reviewed_at) == today,
            )
        )
    )
    rejected_today = rejected_result.scalar() or 0

    # Average review time (for items reviewed in last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)

    avg_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', VideoModeration.reviewed_at) -
                func.extract('epoch', VideoModeration.created_at)
            ) / 3600  # Convert to hours
        ).where(
            and_(
                VideoModeration.reviewed_at.isnot(None),
                VideoModeration.reviewed_at >= week_ago,
            )
        )
    )
    avg_hours = avg_result.scalar() or 0.0

    return ModerationStatsResponse(
        pending_count=pending_count,
        approved_today=approved_today,
        rejected_today=rejected_today,
        avg_review_time_hours=round(avg_hours, 1),
    )


@router.get("/{moderation_id}", response_model=VideoModerationResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_moderation_detail(
    request: Request,
    moderation_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Get details of a specific moderation record.
    """
    query = (
        select(VideoModeration)
        .options(selectinload(VideoModeration.professional).selectinload(ProfessionalProfile.user))
        .where(VideoModeration.id == moderation_id)
    )
    result = await db.execute(query)
    moderation = result.scalar_one_or_none()

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found",
        )

    return VideoModerationResponse(
        id=moderation.id,
        professional_id=moderation.professional_id,
        video_url=moderation.video_url,
        status=moderation.status,
        reviewed_by=moderation.reviewed_by,
        reviewed_at=moderation.reviewed_at,
        rejection_reason=moderation.rejection_reason,
        created_at=moderation.created_at,
        updated_at=moderation.updated_at,
        professional_name=f"{moderation.professional.user.first_name} {moderation.professional.user.last_name}" if moderation.professional and moderation.professional.user else None,
        professional_email=moderation.professional.user.email if moderation.professional and moderation.professional.user else None,
    )
```

3. Register router in `backend/src/app/api/v1/__init__.py`:
```python
from src.app.api.v1.routes.moderation import router as moderation_router

# In the include_routers function:
app.include_router(moderation_router, prefix="/api/v1/moderation", tags=["moderation"])
```

**Acceptance Criteria:**
- [ ] GET /api/v1/moderation/pending returns paginated list of pending videos
- [ ] POST /api/v1/moderation/{id}/approve changes status to approved
- [ ] POST /api/v1/moderation/{id}/reject requires reason and changes status to rejected
- [ ] GET /api/v1/moderation/stats returns accurate counts
- [ ] All endpoints require admin authentication (403 for non-admin)
- [ ] 404 returned for non-existent moderation IDs
- [ ] 400 returned when trying to approve/reject already-reviewed video

**Testing Requirements:**
```python
# backend/tests/test_moderation_api.py

import pytest
from uuid import uuid4

class TestModerationAPI:

    async def test_list_pending_requires_admin(self, client, regular_user_token):
        """Non-admin users should get 403"""
        response = await client.get(
            "/api/v1/moderation/pending",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        assert response.status_code == 403

    async def test_list_pending_returns_fifo_order(self, client, admin_token, pending_videos):
        """Oldest videos should appear first"""
        response = await client.get(
            "/api/v1/moderation/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["created_at"] < data["items"][-1]["created_at"]

    async def test_approve_video_success(self, client, admin_token, pending_video):
        """Approving pending video should update status"""
        response = await client.post(
            f"/api/v1/moderation/{pending_video.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        assert response.json()["reviewed_at"] is not None

    async def test_reject_requires_reason(self, client, admin_token, pending_video):
        """Rejection without reason should fail"""
        response = await client.post(
            f"/api/v1/moderation/{pending_video.id}/reject",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422  # Validation error

    async def test_reject_with_short_reason_fails(self, client, admin_token, pending_video):
        """Reason must be at least 10 characters"""
        response = await client.post(
            f"/api/v1/moderation/{pending_video.id}/reject",
            json={"reason": "Bad"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    async def test_reject_video_success(self, client, admin_token, pending_video):
        """Rejecting with valid reason should work"""
        response = await client.post(
            f"/api/v1/moderation/{pending_video.id}/reject",
            json={"reason": "Video contains inappropriate content that violates community guidelines."},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        assert "inappropriate content" in response.json()["rejection_reason"]

    async def test_cannot_approve_already_approved(self, client, admin_token, approved_video):
        """Cannot approve an already-approved video"""
        response = await client.post(
            f"/api/v1/moderation/{approved_video.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already approved" in response.json()["detail"].lower()
```

**Observability:**
- Log: approval/rejection actions with admin ID and video ID
- Metric: pending_queue_size (gauge)
- Metric: moderation_review_time_seconds (histogram)
- Alert: If pending_queue_size > 100 for 24 hours

**Risks & Mitigations:**
- Risk: Admin approves inappropriate content
- Mitigation: Add audit log showing who approved what, periodic quality review

---

#### TASK 1.1.3: Create Video Moderation Admin UI

**Goal:** Build admin interface for reviewing and moderating video content.

**Scope:**
- INCLUDED: Moderation queue page, video player, approve/reject buttons, rejection reason modal
- EXCLUDED: Video upload (separate feature), user management

**Dependencies:** Task 1.1.2 (API endpoints)

**Prerequisites:**
- Admin dashboard route exists (/dashboard/admin)
- API endpoints working
- Admin authentication working

**Implementation Steps:**

1. Create moderation page at `frontend/src/app/dashboard/admin/moderation/page.tsx`:
```tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api/client';

interface ModerationItem {
  id: string;
  professional_id: string;
  video_url: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  professional_name: string | null;
  professional_email: string | null;
}

interface ModerationStats {
  pending_count: number;
  approved_today: number;
  rejected_today: number;
  avg_review_time_hours: number;
}

export default function ModerationPage() {
  const router = useRouter();
  const { user, isAdmin } = useAuthStore();

  const [items, setItems] = useState<ModerationItem[]>([]);
  const [stats, setStats] = useState<ModerationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedItem, setSelectedItem] = useState<ModerationItem | null>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Redirect non-admins
  useEffect(() => {
    if (!isAdmin) {
      router.push('/dashboard');
    }
  }, [isAdmin, router]);

  // Fetch moderation queue
  useEffect(() => {
    async function fetchQueue() {
      setLoading(true);
      setError(null);
      try {
        const [queueRes, statsRes] = await Promise.all([
          api.get(`/api/v1/moderation/pending?page=${page}&page_size=10`),
          api.get('/api/v1/moderation/stats'),
        ]);
        setItems(queueRes.data.items);
        setTotalPages(queueRes.data.total_pages);
        setStats(statsRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load moderation queue');
      } finally {
        setLoading(false);
      }
    }

    if (isAdmin) {
      fetchQueue();
    }
  }, [page, isAdmin]);

  async function handleApprove(item: ModerationItem) {
    setActionLoading(true);
    try {
      await api.post(`/api/v1/moderation/${item.id}/approve`);
      // Remove from list
      setItems(prev => prev.filter(i => i.id !== item.id));
      // Update stats
      setStats(prev => prev ? {
        ...prev,
        pending_count: prev.pending_count - 1,
        approved_today: prev.approved_today + 1,
      } : null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve video');
    } finally {
      setActionLoading(false);
    }
  }

  function openRejectModal(item: ModerationItem) {
    setSelectedItem(item);
    setRejectReason('');
    setShowRejectModal(true);
  }

  async function handleReject() {
    if (!selectedItem || rejectReason.length < 10) return;

    setActionLoading(true);
    try {
      await api.post(`/api/v1/moderation/${selectedItem.id}/reject`, {
        reason: rejectReason,
      });
      // Remove from list
      setItems(prev => prev.filter(i => i.id !== selectedItem.id));
      // Update stats
      setStats(prev => prev ? {
        ...prev,
        pending_count: prev.pending_count - 1,
        rejected_today: prev.rejected_today + 1,
      } : null);
      setShowRejectModal(false);
      setSelectedItem(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject video');
    } finally {
      setActionLoading(false);
    }
  }

  if (!isAdmin) {
    return null; // Redirecting
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Video Moderation Queue
      </h1>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-yellow-700">{stats.pending_count}</div>
            <div className="text-sm text-yellow-600">Pending Review</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-green-700">{stats.approved_today}</div>
            <div className="text-sm text-green-600">Approved Today</div>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-red-700">{stats.rejected_today}</div>
            <div className="text-sm text-red-600">Rejected Today</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-3xl font-bold text-blue-700">{stats.avg_review_time_hours}h</div>
            <div className="text-sm text-blue-600">Avg Review Time</div>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div role="alert" className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          <span className="font-medium">Error:</span> {error}
          <button
            onClick={() => setError(null)}
            className="float-right text-red-700 hover:text-red-900"
            aria-label="Dismiss error"
          >
            &times;
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" aria-label="Loading"></div>
        </div>
      )}

      {/* Empty State */}
      {!loading && items.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">Queue Empty</h3>
          <p className="mt-1 text-gray-500">All videos have been reviewed. Great work!</p>
        </div>
      )}

      {/* Moderation Queue */}
      {!loading && items.length > 0 && (
        <div className="space-y-6">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
            >
              <div className="flex">
                {/* Video Player */}
                <div className="w-1/2 bg-black">
                  <video
                    src={item.video_url}
                    controls
                    className="w-full h-64 object-contain"
                    preload="metadata"
                  >
                    Your browser does not support video playback.
                  </video>
                </div>

                {/* Info & Actions */}
                <div className="w-1/2 p-6 flex flex-col justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {item.professional_name || 'Unknown Professional'}
                    </h3>
                    <p className="text-sm text-gray-500">{item.professional_email}</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Submitted: {new Date(item.created_at).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-400">
                      Waiting: {Math.round((Date.now() - new Date(item.created_at).getTime()) / (1000 * 60 * 60))} hours
                    </p>
                  </div>

                  <div className="flex space-x-4 mt-4">
                    <button
                      onClick={() => handleApprove(item)}
                      disabled={actionLoading}
                      className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {actionLoading ? 'Processing...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => openRejectModal(item)}
                      disabled={actionLoading}
                      className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-4 mt-8">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedItem && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reject-modal-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h2 id="reject-modal-title" className="text-xl font-bold text-gray-900 mb-4">
              Reject Video
            </h2>
            <p className="text-gray-600 mb-4">
              Please provide a clear reason for rejection. This will be shown to the professional.
            </p>
            <label htmlFor="reject-reason" className="block text-sm font-medium text-gray-700 mb-2">
              Rejection Reason
            </label>
            <textarea
              id="reject-reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-red-500 focus:border-red-500"
              rows={4}
              placeholder="Explain why this video cannot be approved (minimum 10 characters)..."
              minLength={10}
              maxLength={500}
            />
            <p className="text-sm text-gray-500 mt-1">
              {rejectReason.length}/500 characters (minimum 10)
            </p>

            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={rejectReason.length < 10 || actionLoading}
                className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

2. Add navigation link in admin sidebar (in `frontend/src/app/dashboard/admin/layout.tsx` or appropriate navigation component):
```tsx
// Add to admin navigation items:
{
  href: '/dashboard/admin/moderation',
  label: 'Video Moderation',
  icon: 'video', // or appropriate icon
}
```

3. Create keyboard navigation hook for modal:
```tsx
// In the modal, add:
useEffect(() => {
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      setShowRejectModal(false);
    }
  }

  if (showRejectModal) {
    document.addEventListener('keydown', handleKeyDown);
    // Trap focus inside modal
    const modal = document.querySelector('[role="dialog"]');
    if (modal) {
      const focusable = modal.querySelectorAll('button, textarea');
      const first = focusable[0] as HTMLElement;
      first?.focus();
    }
  }

  return () => document.removeEventListener('keydown', handleKeyDown);
}, [showRejectModal]);
```

**Acceptance Criteria:**
- [ ] Page loads and displays pending videos
- [ ] Stats bar shows accurate counts
- [ ] Video player plays uploaded videos
- [ ] Approve button removes video from queue and updates stats
- [ ] Reject button opens modal requiring reason
- [ ] Rejection reason must be 10+ characters
- [ ] Modal closes on Escape key
- [ ] Modal traps focus inside
- [ ] Loading spinner shown while fetching
- [ ] Empty state shown when queue is empty
- [ ] Error messages shown with dismiss option
- [ ] Pagination works correctly
- [ ] Non-admin users redirected to dashboard

**UI/UX Requirements:**
- Loading: Spinner centered on page within 100ms of page load
- Empty: Green checkmark icon + "Queue Empty" message + "Great work!" subtext
- Error: Red alert box with error message and X to dismiss
- Video: Black background, controls visible, aspect ratio preserved
- Approve button: Green background, white text, hover darkens
- Reject button: Red background, white text, hover darkens
- Modal: Centered, backdrop darkened, clear title, textarea with char count
- Stats: 4-column grid on desktop, stack on mobile

**Accessibility:**
- [ ] All buttons have visible focus rings
- [ ] Modal has role="dialog" and aria-modal="true"
- [ ] Modal title has aria-labelledby
- [ ] Error alert has role="alert"
- [ ] Textarea has associated label
- [ ] Video has text fallback

**Testing Requirements:**
```typescript
// frontend/src/app/dashboard/admin/moderation/page.test.tsx

describe('ModerationPage', () => {
  it('redirects non-admin users', async () => {
    // Mock non-admin user
    // Expect router.push to be called with /dashboard
  });

  it('displays pending videos', async () => {
    // Mock API response with 3 pending videos
    // Expect 3 video cards to be rendered
  });

  it('shows loading state initially', () => {
    // Expect spinner to be visible
  });

  it('shows empty state when no pending videos', async () => {
    // Mock empty API response
    // Expect "Queue Empty" message
  });

  it('approves video on button click', async () => {
    // Click approve button
    // Expect API call
    // Expect video removed from list
    // Expect stats updated
  });

  it('opens reject modal with proper focus', async () => {
    // Click reject button
    // Expect modal visible
    // Expect textarea focused
  });

  it('validates rejection reason length', async () => {
    // Enter short reason
    // Expect submit button disabled
    // Enter valid reason
    // Expect submit button enabled
  });

  it('closes modal on Escape key', async () => {
    // Open modal
    // Press Escape
    // Expect modal hidden
  });
});
```

**Observability:**
- Analytics: track_moderation_action(action, video_id, time_to_decision)
- Log: UI errors with component name

**Risks & Mitigations:**
- Risk: Video fails to load
- Mitigation: Show error state with "Video unavailable" message and option to reject with "technical issue" reason

---

#### TASK 1.1.4: Integrate Video Upload with Moderation Queue

**Goal:** When professional uploads a video, automatically create pending moderation record.

**Scope:**
- INCLUDED: Modify video upload endpoint, create moderation record, update grid query
- EXCLUDED: Moderation UI (already built)

**Dependencies:** Tasks 1.1.1, 1.1.2, existing video upload endpoint

**Implementation Steps:**

1. Modify video upload endpoint in `backend/src/app/api/v1/routes/users.py`:
```python
# After successful video upload, add:
from src.app.models.moderation import VideoModeration, ModerationStatus

# Inside the upload_video function, after saving video URL:
moderation = VideoModeration(
    professional_id=current_user.professional_profile.id,
    video_url=video_url,
    status=ModerationStatus.PENDING,
)
db.add(moderation)
await db.commit()

# Return response indicating pending status
return {
    "video_url": video_url,
    "moderation_status": "pending",
    "message": "Video uploaded successfully. It will be visible after admin review."
}
```

2. Update grid query in `backend/src/app/api/v1/routes/professionals.py` to only show approved videos:
```python
# In the grid query, add join/filter:
from src.app.models.moderation import VideoModeration, ModerationStatus

# Subquery to get latest approved video
approved_video_subquery = (
    select(VideoModeration.professional_id)
    .where(VideoModeration.status == ModerationStatus.APPROVED)
    .distinct()
)

# In main query, filter to only include professionals with approved videos OR no video requirement
# (depending on business logic)
```

3. Add moderation status to professional profile response:
```python
# In ProfessionalProfileResponse schema, add:
video_moderation_status: Optional[str] = None  # "pending", "approved", "rejected", or null
```

**Acceptance Criteria:**
- [ ] Video upload creates moderation record
- [ ] Grid only shows professionals with approved videos (or those without video requirement)
- [ ] Professional sees "pending review" status on their profile
- [ ] Professional sees rejection reason if video was rejected

**Testing Requirements:**
- Integration test: Upload video → moderation record created
- Integration test: Grid query excludes pending videos
- Integration test: Grid query excludes rejected videos

---

### EPIC 1.2: Dispute Resolution System

**Goal:** Enable users to submit billing/service disputes and admins to resolve them.

**Current State:** No dispute capability. Users must email support.
**Target State:** In-app dispute form, tracking, resolution workflow, notification on resolution.

---

#### TASK 1.2.1: Create Dispute Data Model

**Goal:** Store dispute tickets with status and resolution history.

**Scope:**
- INCLUDED: Database table, migration, model
- EXCLUDED: API, UI

**Implementation Steps:**

1. Create migration:
```python
# In migration file:
op.create_table(
    'disputes',
    sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
    sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    sa.Column('dispute_type', sa.Enum('billing', 'service', 'technical', 'other', name='dispute_type'), nullable=False),
    sa.Column('subject', sa.String(200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('open', 'in_progress', 'resolved', 'closed', name='dispute_status'), nullable=False, default='open'),
    sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='dispute_priority'), nullable=False, default='medium'),
    sa.Column('related_transaction_id', sa.String(100), nullable=True),  # Stripe transaction ID if billing dispute
    sa.Column('assigned_to', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
)
op.create_index('ix_disputes_user_id', 'disputes', ['user_id'])
op.create_index('ix_disputes_status', 'disputes', ['status'])
op.create_index('ix_disputes_assigned_to', 'disputes', ['assigned_to'])

# Dispute messages table for conversation thread
op.create_table(
    'dispute_messages',
    sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
    sa.Column('dispute_id', sa.UUID(), sa.ForeignKey('disputes.id', ondelete='CASCADE'), nullable=False),
    sa.Column('sender_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_internal', sa.Boolean(), default=False),  # Admin-only notes
    sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
)
op.create_index('ix_dispute_messages_dispute_id', 'dispute_messages', ['dispute_id'])
```

2. Create model in `backend/src/app/models/dispute.py`:
```python
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.app.core.database import Base


class DisputeType(str, PyEnum):
    BILLING = "billing"
    SERVICE = "service"
    TECHNICAL = "technical"
    OTHER = "other"


class DisputeStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputePriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dispute_type = Column(Enum(DisputeType), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(DisputeStatus), nullable=False, default=DisputeStatus.OPEN)
    priority = Column(Enum(DisputePriority), nullable=False, default=DisputePriority.MEDIUM)
    related_transaction_id = Column(String(100), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="disputes")
    assignee = relationship("User", foreign_keys=[assigned_to])
    messages = relationship("DisputeMessage", back_populates="dispute", order_by="DisputeMessage.created_at")


class DisputeMessage(Base):
    __tablename__ = "dispute_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dispute_id = Column(UUID(as_uuid=True), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    dispute = relationship("Dispute", back_populates="messages")
    sender = relationship("User")
```

**Acceptance Criteria:**
- [ ] Migration runs without errors
- [ ] Both tables created with indexes
- [ ] Relationships work correctly
- [ ] Enum values work correctly

---

#### TASK 1.2.2: Create Dispute API Endpoints

**Goal:** REST API for creating, viewing, and managing disputes.

**Scope:**
- INCLUDED: User endpoints (create, list my disputes, add message), Admin endpoints (list all, assign, resolve)
- EXCLUDED: UI

**Implementation Steps:**

1. Create schemas in `backend/src/app/schemas/dispute.py`:
```python
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from src.app.models.dispute import DisputeType, DisputeStatus, DisputePriority


class CreateDisputeRequest(BaseModel):
    dispute_type: DisputeType
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    related_transaction_id: Optional[str] = None


class AddMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False  # Only admins can set this to True


class ResolveDisputeRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=10, max_length=2000)


class AssignDisputeRequest(BaseModel):
    assigned_to: UUID


class DisputeMessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    sender_name: Optional[str] = None
    message: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DisputeResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    dispute_type: DisputeType
    subject: str
    description: str
    status: DisputeStatus
    priority: DisputePriority
    related_transaction_id: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages: List[DisputeMessageResponse] = []

    class Config:
        from_attributes = True


class DisputeListResponse(BaseModel):
    items: List[DisputeResponse]
    total: int
    page: int
    page_size: int
```

2. Create router in `backend/src/app/api/v1/routes/disputes.py`:
```python
"""
Dispute Resolution API routes.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Request, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from src.app.core.dependencies import DbSession, CurrentUser, CurrentAdmin
from src.app.core.rate_limit import limiter, RATE_LIMITS
from src.app.models.dispute import Dispute, DisputeMessage, DisputeStatus, DisputePriority
from src.app.models.user import User
from src.app.schemas.dispute import (
    CreateDisputeRequest,
    AddMessageRequest,
    ResolveDisputeRequest,
    AssignDisputeRequest,
    DisputeResponse,
    DisputeMessageResponse,
    DisputeListResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== User Endpoints ====================

@router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["api_write"])
async def create_dispute(
    request: Request,
    body: CreateDisputeRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Create a new dispute ticket.

    Users can submit disputes for billing issues, service complaints,
    technical problems, or other concerns.
    """
    dispute = Dispute(
        user_id=current_user.id,
        dispute_type=body.dispute_type,
        subject=body.subject,
        description=body.description,
        related_transaction_id=body.related_transaction_id,
        status=DisputeStatus.OPEN,
        priority=DisputePriority.MEDIUM,
    )
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute.id} created by user {current_user.id}")

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        related_transaction_id=dispute.related_transaction_id,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        messages=[],
    )


@router.get("/my", response_model=DisputeListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_my_disputes(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Optional[DisputeStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List current user's disputes.
    """
    query = select(Dispute).where(Dispute.user_id == current_user.id)

    if status_filter:
        query = query.where(Dispute.status == status_filter)

    # Count
    count_query = select(func.count(Dispute.id)).where(Dispute.user_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Dispute.status == status_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch
    query = query.order_by(Dispute.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    result = await db.execute(query)
    disputes = result.scalars().all()

    return DisputeListResponse(
        items=[DisputeResponse(
            id=d.id,
            user_id=d.user_id,
            dispute_type=d.dispute_type,
            subject=d.subject,
            description=d.description,
            status=d.status,
            priority=d.priority,
            related_transaction_id=d.related_transaction_id,
            assigned_to=d.assigned_to,
            resolution_notes=d.resolution_notes,
            resolved_at=d.resolved_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
        ) for d in disputes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dispute_id}", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def get_dispute(
    request: Request,
    dispute_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Get dispute details with message history.

    Users can only view their own disputes. Admins can view any.
    """
    query = (
        select(Dispute)
        .options(selectinload(Dispute.messages).selectinload(DisputeMessage.sender))
        .options(selectinload(Dispute.user))
        .options(selectinload(Dispute.assignee))
        .where(Dispute.id == dispute_id)
    )
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    # Check access
    is_admin = getattr(current_user, 'is_admin', False)
    if dispute.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Filter internal messages for non-admins
    messages = []
    for m in dispute.messages:
        if m.is_internal and not is_admin:
            continue
        messages.append(DisputeMessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            sender_name=f"{m.sender.first_name} {m.sender.last_name}" if m.sender else None,
            message=m.message,
            is_internal=m.is_internal,
            created_at=m.created_at,
        ))

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        user_name=f"{dispute.user.first_name} {dispute.user.last_name}" if dispute.user else None,
        user_email=dispute.user.email if dispute.user else None,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        related_transaction_id=dispute.related_transaction_id,
        assigned_to=dispute.assigned_to,
        assignee_name=f"{dispute.assignee.first_name} {dispute.assignee.last_name}" if dispute.assignee else None,
        resolution_notes=dispute.resolution_notes,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        messages=messages,
    )


@router.post("/{dispute_id}/messages", response_model=DisputeMessageResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def add_message(
    request: Request,
    dispute_id: UUID,
    body: AddMessageRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Add a message to a dispute thread.

    Users can only message on their own disputes.
    Admins can message on any dispute and mark messages as internal.
    """
    query = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    is_admin = getattr(current_user, 'is_admin', False)
    if dispute.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only admins can mark internal
    is_internal = body.is_internal and is_admin

    message = DisputeMessage(
        dispute_id=dispute_id,
        sender_id=current_user.id,
        message=body.message,
        is_internal=is_internal,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return DisputeMessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=f"{current_user.first_name} {current_user.last_name}",
        message=message.message,
        is_internal=message.is_internal,
        created_at=message.created_at,
    )


# ==================== Admin Endpoints ====================

@router.get("/admin/all", response_model=DisputeListResponse)
@limiter.limit(RATE_LIMITS["api_read"])
async def list_all_disputes(
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    status_filter: Optional[DisputeStatus] = None,
    priority_filter: Optional[DisputePriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all disputes (admin only).

    Supports filtering by status and priority.
    """
    query = select(Dispute).options(selectinload(Dispute.user))
    count_query = select(func.count(Dispute.id))

    if status_filter:
        query = query.where(Dispute.status == status_filter)
        count_query = count_query.where(Dispute.status == status_filter)

    if priority_filter:
        query = query.where(Dispute.priority == priority_filter)
        count_query = count_query.where(Dispute.priority == priority_filter)

    # Count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch with priority ordering (urgent first)
    priority_order = {
        DisputePriority.URGENT: 1,
        DisputePriority.HIGH: 2,
        DisputePriority.MEDIUM: 3,
        DisputePriority.LOW: 4,
    }
    query = query.order_by(Dispute.priority, Dispute.created_at.asc()).offset((page-1)*page_size).limit(page_size)
    result = await db.execute(query)
    disputes = result.scalars().all()

    return DisputeListResponse(
        items=[DisputeResponse(
            id=d.id,
            user_id=d.user_id,
            user_name=f"{d.user.first_name} {d.user.last_name}" if d.user else None,
            user_email=d.user.email if d.user else None,
            dispute_type=d.dispute_type,
            subject=d.subject,
            description=d.description,
            status=d.status,
            priority=d.priority,
            related_transaction_id=d.related_transaction_id,
            assigned_to=d.assigned_to,
            resolution_notes=d.resolution_notes,
            resolved_at=d.resolved_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
        ) for d in disputes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{dispute_id}/assign", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def assign_dispute(
    request: Request,
    dispute_id: UUID,
    body: AssignDisputeRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Assign a dispute to an admin user.
    """
    query = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute.assigned_to = body.assigned_to
    dispute.status = DisputeStatus.IN_PROGRESS
    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute_id} assigned to {body.assigned_to} by {current_admin.id}")

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        assigned_to=dispute.assigned_to,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
    )


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
@limiter.limit(RATE_LIMITS["api_write"])
async def resolve_dispute(
    request: Request,
    dispute_id: UUID,
    body: ResolveDisputeRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """
    Resolve a dispute with resolution notes.

    User will be notified of resolution.
    """
    query = select(Dispute).where(Dispute.id == dispute_id)
    result = await db.execute(query)
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution_notes = body.resolution_notes
    dispute.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(dispute)

    logger.info(f"Dispute {dispute_id} resolved by {current_admin.id}")

    # TODO: Send notification to user about resolution

    return DisputeResponse(
        id=dispute.id,
        user_id=dispute.user_id,
        dispute_type=dispute.dispute_type,
        subject=dispute.subject,
        description=dispute.description,
        status=dispute.status,
        priority=dispute.priority,
        resolution_notes=dispute.resolution_notes,
        resolved_at=dispute.resolved_at,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
    )
```

3. Register router in main app.

**Acceptance Criteria:**
- [ ] Users can create disputes
- [ ] Users can list their own disputes
- [ ] Users can view dispute details with messages
- [ ] Users can add messages to their disputes
- [ ] Admins can list all disputes
- [ ] Admins can assign disputes
- [ ] Admins can resolve disputes
- [ ] Internal messages hidden from users

---

#### TASK 1.2.3: Create Dispute UI for Users

**Goal:** Allow users to submit and track their disputes.

**Scope:**
- INCLUDED: Submit dispute form, list my disputes, view dispute detail with messages
- EXCLUDED: Admin UI (separate task)

**Implementation Steps:**

1. Create dispute submission page at `frontend/src/app/dashboard/support/disputes/new/page.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api/client';

type DisputeType = 'billing' | 'service' | 'technical' | 'other';

export default function NewDisputePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [disputeType, setDisputeType] = useState<DisputeType>('billing');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [transactionId, setTransactionId] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (subject.length < 5) {
      setError('Subject must be at least 5 characters');
      return;
    }
    if (description.length < 20) {
      setError('Description must be at least 20 characters');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/disputes', {
        dispute_type: disputeType,
        subject,
        description,
        related_transaction_id: transactionId || undefined,
      });

      router.push(`/dashboard/support/disputes/${response.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit dispute');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Submit a Dispute</h1>
      <p className="text-gray-600 mb-8">
        Having an issue? We're here to help. Please provide details below and we'll respond within 24 hours.
      </p>

      {error && (
        <div role="alert" className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Dispute Type */}
        <div>
          <label htmlFor="dispute-type" className="block text-sm font-medium text-gray-700 mb-2">
            What type of issue is this?
          </label>
          <select
            id="dispute-type"
            value={disputeType}
            onChange={(e) => setDisputeType(e.target.value as DisputeType)}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="billing">Billing Issue</option>
            <option value="service">Service Complaint</option>
            <option value="technical">Technical Problem</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Transaction ID (for billing) */}
        {disputeType === 'billing' && (
          <div>
            <label htmlFor="transaction-id" className="block text-sm font-medium text-gray-700 mb-2">
              Transaction ID (optional)
            </label>
            <input
              type="text"
              id="transaction-id"
              value={transactionId}
              onChange={(e) => setTransactionId(e.target.value)}
              placeholder="e.g., txn_1234567890"
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              You can find this in your billing history or payment receipt.
            </p>
          </div>
        )}

        {/* Subject */}
        <div>
          <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
            Subject
          </label>
          <input
            type="text"
            id="subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Brief summary of your issue"
            maxLength={200}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            {subject.length}/200 characters (minimum 5)
          </p>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Please provide as much detail as possible..."
            rows={6}
            maxLength={5000}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            {description.length}/5000 characters (minimum 20)
          </p>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || subject.length < 5 || description.length < 20}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Submitting...' : 'Submit Dispute'}
        </button>
      </form>
    </div>
  );
}
```

2. Create disputes list page at `frontend/src/app/dashboard/support/disputes/page.tsx`:
```tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/client';

interface Dispute {
  id: string;
  dispute_type: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
  resolved_at: string | null;
}

export default function DisputesListPage() {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDisputes() {
      try {
        const response = await api.get('/api/v1/disputes/my');
        setDisputes(response.data.items);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load disputes');
      } finally {
        setLoading(false);
      }
    }
    fetchDisputes();
  }, []);

  const statusColors = {
    open: 'bg-yellow-100 text-yellow-800',
    in_progress: 'bg-blue-100 text-blue-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Disputes</h1>
        <Link
          href="/dashboard/support/disputes/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + New Dispute
        </Link>
      </div>

      {error && (
        <div role="alert" className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" aria-label="Loading"></div>
        </div>
      )}

      {!loading && disputes.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No disputes</h3>
          <p className="mt-1 text-gray-500">You haven't submitted any disputes yet.</p>
          <Link
            href="/dashboard/support/disputes/new"
            className="inline-block mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Submit a Dispute
          </Link>
        </div>
      )}

      {!loading && disputes.length > 0 && (
        <div className="space-y-4">
          {disputes.map((dispute) => (
            <Link
              key={dispute.id}
              href={`/dashboard/support/disputes/${dispute.id}`}
              className="block bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-gray-900">{dispute.subject}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {dispute.dispute_type.charAt(0).toUpperCase() + dispute.dispute_type.slice(1)} &middot; {new Date(dispute.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[dispute.status as keyof typeof statusColors]}`}>
                  {dispute.status.replace('_', ' ')}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

3. Create dispute detail page at `frontend/src/app/dashboard/support/disputes/[id]/page.tsx`:
```tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { useAuthStore } from '@/stores/authStore';

interface DisputeMessage {
  id: string;
  sender_id: string;
  sender_name: string | null;
  message: string;
  is_internal: boolean;
  created_at: string;
}

interface Dispute {
  id: string;
  dispute_type: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  resolution_notes: string | null;
  resolved_at: string | null;
  created_at: string;
  messages: DisputeMessage[];
}

export default function DisputeDetailPage() {
  const params = useParams();
  const { user } = useAuthStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  useEffect(() => {
    async function fetchDispute() {
      try {
        const response = await api.get(`/api/v1/disputes/${params.id}`);
        setDispute(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dispute');
      } finally {
        setLoading(false);
      }
    }
    fetchDispute();
  }, [params.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dispute?.messages]);

  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSendingMessage(true);
    try {
      const response = await api.post(`/api/v1/disputes/${params.id}/messages`, {
        message: newMessage,
      });
      setDispute(prev => prev ? {
        ...prev,
        messages: [...prev.messages, response.data],
      } : null);
      setNewMessage('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  }

  const statusColors = {
    open: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    in_progress: 'bg-blue-100 text-blue-800 border-blue-200',
    resolved: 'bg-green-100 text-green-800 border-green-200',
    closed: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" aria-label="Loading"></div>
      </div>
    );
  }

  if (error || !dispute) {
    return (
      <div role="alert" className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error || 'Dispute not found'}
        </div>
      </div>
    );
  }

  const isResolved = dispute.status === 'resolved' || dispute.status === 'closed';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className={`px-3 py-1 text-sm font-medium rounded-full border ${statusColors[dispute.status as keyof typeof statusColors]}`}>
            {dispute.status.replace('_', ' ')}
          </span>
          <span className="text-sm text-gray-500">
            {dispute.dispute_type.charAt(0).toUpperCase() + dispute.dispute_type.slice(1)}
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{dispute.subject}</h1>
        <p className="text-sm text-gray-500 mt-1">
          Submitted on {new Date(dispute.created_at).toLocaleString()}
        </p>
      </div>

      {/* Original Description */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Original Description</h3>
        <p className="text-gray-600 whitespace-pre-wrap">{dispute.description}</p>
      </div>

      {/* Resolution (if resolved) */}
      {dispute.resolution_notes && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-medium text-green-800 mb-2">Resolution</h3>
          <p className="text-green-700 whitespace-pre-wrap">{dispute.resolution_notes}</p>
          {dispute.resolved_at && (
            <p className="text-sm text-green-600 mt-2">
              Resolved on {new Date(dispute.resolved_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Message Thread */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="font-medium text-gray-900">Conversation</h3>
        </div>

        <div className="max-h-96 overflow-y-auto p-4 space-y-4">
          {dispute.messages.length === 0 ? (
            <p className="text-center text-gray-500 py-4">No messages yet</p>
          ) : (
            dispute.messages.map((msg) => {
              const isOwnMessage = msg.sender_id === user?.id;
              return (
                <div
                  key={msg.id}
                  className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      isOwnMessage
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className={`text-xs mb-1 ${isOwnMessage ? 'text-blue-200' : 'text-gray-500'}`}>
                      {msg.sender_name || 'Support'} &middot; {new Date(msg.created_at).toLocaleTimeString()}
                    </p>
                    <p className="whitespace-pre-wrap">{msg.message}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        {!isResolved && (
          <form onSubmit={handleSendMessage} className="border-t border-gray-200 p-4">
            <div className="flex gap-3">
              <label htmlFor="new-message" className="sr-only">New message</label>
              <input
                type="text"
                id="new-message"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={!newMessage.trim() || sendingMessage}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {sendingMessage ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        )}

        {isResolved && (
          <div className="border-t border-gray-200 p-4 bg-gray-50 text-center text-gray-500">
            This dispute has been resolved. If you have additional concerns, please open a new dispute.
          </div>
        )}
      </div>
    </div>
  );
}
```

**Acceptance Criteria:**
- [ ] Users can access dispute form from support menu
- [ ] Form validates all fields before submission
- [ ] Users can view list of their disputes
- [ ] Users can click into dispute to see details
- [ ] Users can send messages on open disputes
- [ ] Messages appear in real-time after sending
- [ ] Resolved disputes show resolution notes
- [ ] Message input disabled on resolved disputes

---

[CONTINUING WITH REMAINING EPICS AND PHASES...]

---

### EPIC 1.3: Pre-recorded Video Upload UI

**Goal:** Enable professionals to upload intro videos for their grid card.

*(Task details follow same structure as above - abbreviated for length)*

---

### EPIC 1.4: Email Verification UI

**Goal:** Show verification status and allow resending verification emails.

---

### EPIC 1.5: User Management Admin

**Goal:** Allow admins to search, view, and manage user accounts.

---

### EPIC 1.6: Legal Pages Content

**Goal:** Add real Privacy Policy and Terms of Service content.

---

### EPIC 1.7: Audit Log Viewer

**Goal:** Provide admin interface to view system audit logs.

---

## PHASE 2: HIGH PRIORITY IMPROVEMENTS

**Duration:** 2 weeks
**Goal:** Close all UX 4-6 gaps

### EPIC 2.1: Push Notifications (Full Implementation)
### EPIC 2.2: Admin Dashboard Enhancement
### EPIC 2.3: Comparative Benchmarks Dashboard

---

## PHASE 3: FEATURE COMPLETIONS

**Duration:** 2 weeks
**Goal:** Complete all partial implementations

### EPIC 3.1: OAuth Completion
### EPIC 3.2: Call Quality Metrics Display
### EPIC 3.3: Missed Call Notifications
### EPIC 3.4: Lead Export UI
### EPIC 3.5: Notification Preferences UI
### EPIC 3.6: Commission Tracking UI
### EPIC 3.7: System Health Dashboard
### EPIC 3.8: Account Deletion UX

---

## PHASE 4: NEW FEATURES

**Duration:** 2 weeks
**Goal:** Implement missing vision features

### EPIC 4.1: SMS Notifications (Twilio)
### EPIC 4.2: Lead Import
### EPIC 4.3: Lead Scoring
### EPIC 4.4: Report Export (PDF/CSV)
### EPIC 4.5: Data Export (GDPR)
### EPIC 4.6: Call Recording Playback

---

## PHASE 5: POLISH

**Duration:** 2 weeks
**Goal:** Raise all UX 7-9 features to 10

### EPIC 5.1: Password Reset Flow Enhancement
### EPIC 5.2: Video Preview Optimization
### EPIC 5.3: Schedule Call Refinement
### EPIC 5.4: Screen Sharing UX
### EPIC 5.5: Bid Wallet UX
### EPIC 5.6: All Remaining Polish Items

---

## PHASE 6: TESTING & HARDENING

**Duration:** 1 week
**Goal:** Comprehensive testing, performance optimization, security audit

### EPIC 6.1: E2E Test Coverage
### EPIC 6.2: Performance Optimization
### EPIC 6.3: Security Audit
### EPIC 6.4: Accessibility Audit

---

## TOP 10 HIGHEST-LEVERAGE IMPROVEMENTS

| Rank | Improvement | Current UX | Effort | Impact | ROI |
|------|-------------|-----------|--------|--------|-----|
| 1 | Pre-recorded Video Upload UI | 2 | 3 days | Critical - Core feature unusable | Very High |
| 2 | Content Moderation System | 0 | 5 days | Critical - Trust & safety | Very High |
| 3 | Email Verification UI | 2 | 2 days | Critical - Security | High |
| 4 | Dispute Resolution System | 0 | 5 days | Critical - Customer support | High |
| 5 | Push Notifications | 4 | 3 days | High - Engagement driver | High |
| 6 | Privacy/Terms Content | 3 | 1 day | Critical - Legal | Very High |
| 7 | Admin Dashboard | 4 | 4 days | Medium - Operations | Medium |
| 8 | User Management | 2 | 3 days | Medium - Support ops | Medium |
| 9 | Call Quality Indicators | 5 | 2 days | Medium - UX | Medium |
| 10 | Lead Export UI | 5 | 1 day | Medium - CRM integration | High |

---

## ROLLOUT PLAN

### Stage 1: Local Development
- All developers pull latest, run migrations
- Manual testing of each feature against acceptance criteria
- Code review by senior developer

### Stage 2: Staging Environment
- Deploy to staging.facemortgage.com
- Run full E2E test suite
- QA team performs manual exploratory testing
- Accessibility audit with axe-core
- Performance testing with Lighthouse
- Security scan with OWASP ZAP
- Duration: 3-5 days per phase

### Stage 3: QA Sign-off Checklist
- [ ] All E2E tests passing
- [ ] No P0/P1 bugs open
- [ ] Accessibility score > 90
- [ ] Performance score > 80
- [ ] Security scan clean
- [ ] Product owner demo approval
- [ ] Release notes drafted

### Stage 4: Production Deployment
- Deploy during low-traffic window (Tuesday 2am ET)
- Feature flags for major features (gradual rollout)
- Rollout to 10% → 50% → 100% over 48 hours
- Monitor error rates, latency, user feedback
- Rollback plan: Single-command revert to previous version

### Stage 5: Post-Deployment
- Monitor for 24 hours
- Respond to user feedback
- Hotfix critical issues immediately
- Retrospective within 1 week

---

## APPENDIX A: Test Case Examples

### Content Moderation E2E Test
```typescript
describe('Content Moderation Flow', () => {
  it('complete moderation workflow', async () => {
    // 1. Professional uploads video
    await loginAs('professional');
    await page.goto('/dashboard/settings');
    await page.click('tab[data-id="video"]');
    await page.setInputFiles('input[type="file"]', 'test-video.mp4');
    await page.click('button:has-text("Upload")');
    await expect(page.locator('.upload-success')).toBeVisible();

    // 2. Video not in grid yet
    await page.goto('/');
    await expect(page.locator(`[data-professional-id="${professionalId}"]`)).not.toBeVisible();

    // 3. Admin reviews and approves
    await loginAs('admin');
    await page.goto('/dashboard/admin/moderation');
    await expect(page.locator('.video-card')).toBeVisible();
    await page.click('button:has-text("Approve")');
    await expect(page.locator('.video-card')).not.toBeVisible();

    // 4. Video now in grid
    await page.goto('/');
    await expect(page.locator(`[data-professional-id="${professionalId}"]`)).toBeVisible();
  });
});
```

---

## APPENDIX B: Database Schema Changes Summary

| Table | Action | Phase |
|-------|--------|-------|
| video_moderations | CREATE | 1 |
| disputes | CREATE | 1 |
| dispute_messages | CREATE | 1 |
| audit_logs | CREATE | 1 |
| notification_preferences | ALTER (add columns) | 2 |
| push_subscriptions | CREATE | 2 |
| lead_scores | CREATE | 4 |
| sms_messages | CREATE | 4 |

---

## APPENDIX C: API Endpoints Summary

| Endpoint | Method | Auth | Phase |
|----------|--------|------|-------|
| /api/v1/moderation/pending | GET | Admin | 1 |
| /api/v1/moderation/{id}/approve | POST | Admin | 1 |
| /api/v1/moderation/{id}/reject | POST | Admin | 1 |
| /api/v1/disputes | POST | User | 1 |
| /api/v1/disputes/my | GET | User | 1 |
| /api/v1/disputes/{id} | GET | User/Admin | 1 |
| /api/v1/disputes/{id}/messages | POST | User/Admin | 1 |
| /api/v1/disputes/admin/all | GET | Admin | 1 |
| /api/v1/disputes/{id}/resolve | POST | Admin | 1 |
| /api/v1/users/me/verify-email | POST | User | 1 |
| /api/v1/users/me/resend-verification | POST | User | 1 |
| /api/v1/admin/users | GET | Admin | 1 |
| /api/v1/admin/users/{id} | GET/PATCH | Admin | 1 |
| /api/v1/audit-logs | GET | Admin | 1 |
| /api/v1/push/subscribe | POST | User | 2 |
| /api/v1/push/unsubscribe | POST | User | 2 |
| /api/v1/analytics/benchmarks | GET | Professional | 2 |
| /api/v1/leads/export | GET | Professional | 3 |
| /api/v1/leads/import | POST | Professional | 4 |
| /api/v1/sms/send | POST | System | 4 |
| /api/v1/reports/generate | POST | Professional | 4 |
| /api/v1/users/me/data-export | POST | User | 4 |

---

**END OF IMPLEMENTATION PLAN**
