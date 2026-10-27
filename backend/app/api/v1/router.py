from fastapi import APIRouter

from app.api.v1.actions import router as actions_router
from app.api.v1.hackathons import router as hackathons_router
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.news import router as news_router
from app.api.v1.stats import router as stats_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(news_router, prefix="/news", tags=["news"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(hackathons_router, prefix="/hackathons", tags=["hackathons"])
api_router.include_router(actions_router, prefix="/actions", tags=["actions"])
api_router.include_router(stats_router, prefix="/admin", tags=["admin"])
