"""
Grid tracking API routes for recording impressions and clicks.

These endpoints enable analytics tracking for the professional grid.
"""
import logging
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.app.core.dependencies import DbSession, CurrentUserOptional
from src.app.models.analytics import GridImpression, GridClick

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class ImpressionItem(BaseModel):
    """Single impression record."""
    professional_id: UUID
    position: int = Field(..., ge=1, description="Grid position when shown")


class TrackImpressionsRequest(BaseModel):
    """Request to track multiple grid impressions at once."""
    impressions: List[ImpressionItem] = Field(..., max_length=100)
    session_id: Optional[str] = None


class TrackClickRequest(BaseModel):
    """Request to track a single grid click."""
    professional_id: UUID
    click_type: str = Field(
        ...,
        description="Type of click: profile_view, call_initiated, video_preview"
    )
    grid_position: Optional[int] = Field(None, ge=1)
    session_id: Optional[str] = None
    filter_context: Optional[dict] = Field(
        None,
        description="Filters that were active when clicked"
    )


class TrackingResponse(BaseModel):
    """Response for tracking endpoints."""
    success: bool
    tracked_count: int = 0
    message: str = "Tracked successfully"


# ==================== Endpoints ====================

@router.post("/track-impressions", response_model=TrackingResponse)
async def track_impressions(
    request_data: TrackImpressionsRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUserOptional,
    x_session_id: Optional[str] = Header(None),
):
    """
    Track when professional cards are shown in the grid.

    This endpoint aggregates impressions daily per professional.
    Called when the grid loads or when user scrolls to reveal new cards.
    """
    if not request_data.impressions:
        return TrackingResponse(success=True, tracked_count=0, message="No impressions to track")

    today = date.today()
    session_id = request_data.session_id or x_session_id

    try:
        # Group impressions by professional_id for aggregation
        impression_counts = {}
        position_totals = {}

        for imp in request_data.impressions:
            prof_id = str(imp.professional_id)
            impression_counts[prof_id] = impression_counts.get(prof_id, 0) + 1
            # Track positions for average calculation
            if prof_id not in position_totals:
                position_totals[prof_id] = []
            position_totals[prof_id].append(imp.position)

        # Upsert impressions for each professional
        for prof_id, count in impression_counts.items():
            avg_pos = sum(position_totals[prof_id]) // len(position_totals[prof_id])

            # Use PostgreSQL upsert for efficiency
            stmt = insert(GridImpression).values(
                professional_id=UUID(prof_id),
                date=today,
                impressions_count=count,
                clicks_count=0,
                calls_initiated=0,
                avg_position=avg_pos,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ).on_conflict_do_update(
                index_elements=['professional_id', 'date'],
                set_={
                    'impressions_count': GridImpression.impressions_count + count,
                    'avg_position': avg_pos,  # Could use weighted average here
                    'updated_at': datetime.utcnow(),
                }
            )
            await db.execute(stmt)

        await db.commit()

        return TrackingResponse(
            success=True,
            tracked_count=len(request_data.impressions),
            message=f"Tracked {len(request_data.impressions)} impressions"
        )

    except Exception as e:
        logger.warning(f"Failed to track impressions: {e}")
        await db.rollback()
        return TrackingResponse(
            success=False,
            tracked_count=0,
            message="Failed to track impressions"
        )


@router.post("/track-click", response_model=TrackingResponse)
async def track_click(
    request_data: TrackClickRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUserOptional,
    x_session_id: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
):
    """
    Track when a user clicks on a professional card.

    Click types:
    - profile_view: Clicked to view full profile
    - call_initiated: Clicked to start a call
    - video_preview: Clicked to preview video
    """
    today = date.today()
    session_id = request_data.session_id or x_session_id

    # Get client IP (handle proxies)
    ip_address = None
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host

    # Validate click_type
    valid_click_types = ["profile_view", "call_initiated", "video_preview"]
    if request_data.click_type not in valid_click_types:
        return TrackingResponse(
            success=False,
            message=f"Invalid click_type. Must be one of: {valid_click_types}"
        )

    try:
        # Create detailed click record
        click = GridClick(
            professional_id=request_data.professional_id,
            borrower_id=current_user.id if current_user else None,
            session_id=session_id,
            click_type=request_data.click_type,
            grid_position=request_data.grid_position,
            filter_context=request_data.filter_context,
            referrer=request.headers.get("referer"),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(click)

        # Also update daily aggregation for clicks
        stmt = insert(GridImpression).values(
            professional_id=request_data.professional_id,
            date=today,
            impressions_count=0,
            clicks_count=1,
            calls_initiated=1 if request_data.click_type == "call_initiated" else 0,
            avg_position=request_data.grid_position,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ).on_conflict_do_update(
            index_elements=['professional_id', 'date'],
            set_={
                'clicks_count': GridImpression.clicks_count + 1,
                'calls_initiated': GridImpression.calls_initiated + (
                    1 if request_data.click_type == "call_initiated" else 0
                ),
                'updated_at': datetime.utcnow(),
            }
        )
        await db.execute(stmt)

        await db.commit()

        logger.debug(
            f"Tracked click: {request_data.click_type} on professional "
            f"{request_data.professional_id} at position {request_data.grid_position}"
        )

        return TrackingResponse(
            success=True,
            tracked_count=1,
            message=f"Tracked {request_data.click_type} click"
        )

    except Exception as e:
        logger.warning(f"Failed to track click: {e}")
        await db.rollback()
        return TrackingResponse(
            success=False,
            tracked_count=0,
            message="Failed to track click"
        )


@router.get("/stats/today")
async def get_today_stats(
    db: DbSession,
):
    """
    Get aggregate grid stats for today.

    Useful for monitoring and real-time dashboards.
    """
    from sqlalchemy import func

    today = date.today()

    result = await db.execute(
        select(
            func.sum(GridImpression.impressions_count).label("total_impressions"),
            func.sum(GridImpression.clicks_count).label("total_clicks"),
            func.sum(GridImpression.calls_initiated).label("total_calls"),
            func.count(GridImpression.id).label("unique_professionals_shown"),
        )
        .where(GridImpression.date == today)
    )

    row = result.one()

    total_impressions = row.total_impressions or 0
    total_clicks = row.total_clicks or 0

    return {
        "date": today.isoformat(),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_calls_initiated": row.total_calls or 0,
        "unique_professionals_shown": row.unique_professionals_shown or 0,
        "click_through_rate": (
            round(total_clicks / total_impressions * 100, 2)
            if total_impressions > 0 else 0
        ),
    }
