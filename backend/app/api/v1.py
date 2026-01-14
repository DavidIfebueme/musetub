from fastapi import APIRouter

from app.features.auth.routes import router as auth_router
from app.features.content.routes import router as content_router
from app.features.health.routes import router as health_router
from app.features.payments.routes import router as payments_router
from app.features.users.routes import router as users_router
from app.features.wallets.routes import router as wallets_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, tags=["auth"])
api_v1_router.include_router(users_router, tags=["users"])
api_v1_router.include_router(wallets_router, tags=["wallets"])
api_v1_router.include_router(content_router, tags=["content"])
api_v1_router.include_router(payments_router, tags=["payments"])
