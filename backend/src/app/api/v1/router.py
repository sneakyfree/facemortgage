from fastapi import APIRouter

from src.app.api.v1.routes import (
    auth, users, professionals, lookups, videos, calls, billing, stats,
    leads, analytics, admin, grid, scheduled_calls, soft_leads, partnerships,
    devices, health, moderation, disputes, audit, oauth, exports, thumbnails, sms,
    nmls, matching, grid_enhanced, billing_enhanced, agentic, performance, bid
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
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
api_router.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
api_router.include_router(disputes.router, prefix="/disputes", tags=["disputes"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(thumbnails.router, prefix="/thumbnails", tags=["thumbnails"])
api_router.include_router(sms.router, tags=["sms"])
api_router.include_router(nmls.router, prefix="/nmls", tags=["nmls-verification"])
api_router.include_router(matching.router, prefix="/matching", tags=["borrower-matching"])
api_router.include_router(grid_enhanced.router, prefix="/grid-enhanced", tags=["grid-enhanced"])
api_router.include_router(billing_enhanced.router, prefix="/billing-enhanced", tags=["billing-enhanced"])
api_router.include_router(agentic.router, prefix="/agentic", tags=["agentic-intelligence"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(bid.router, prefix="/bid", tags=["bid-wallet"])
