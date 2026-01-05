from fastapi import APIRouter

from src.app.api.v1.routes import (
    auth, users, professionals, lookups, videos, calls, billing, stats,
    leads, analytics, admin, grid, scheduled_calls, soft_leads, partnerships,
    devices, health
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(professionals.router, prefix="/professionals", tags=["professionals"])
api_router.include_router(lookups.router, prefix="/lookups", tags=["lookups"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(stats.router, prefix="/stats", tags=["professional-stats"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(grid.router, prefix="/grid", tags=["grid-tracking"])
api_router.include_router(scheduled_calls.router, prefix="/scheduled-calls", tags=["scheduled-calls"])
api_router.include_router(soft_leads.router, prefix="/soft-leads", tags=["soft-leads"])
api_router.include_router(partnerships.router, prefix="/partnerships", tags=["partnerships"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
