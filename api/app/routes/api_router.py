from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.health_controller import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
