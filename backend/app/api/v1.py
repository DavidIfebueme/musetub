from fastapi import APIRouter

from app.features.auth.routes import router as auth_router
from app.features.health.routes import router as health_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, tags=["auth"])
