"""API v1 route aggregation."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.websites import router as websites_router
from app.api.v1.audits import router as audits_router
from app.api.v1.reports import router as reports_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.exports import router as exports_router

api_v1_router = APIRouter()


@api_v1_router.get("/health", tags=["Health"])
async def api_v1_health():
    return {"status": "healthy"}


api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
api_v1_router.include_router(websites_router, prefix="/websites", tags=["Websites"])
api_v1_router.include_router(audits_router, prefix="/audits", tags=["Audits"])
api_v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(exports_router, prefix="/exports", tags=["Exports"])
