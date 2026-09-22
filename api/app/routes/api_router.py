from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.checkout_controller import router as checkout_router
from app.controllers.demo_controller import router as demo_router
from app.controllers.health_controller import router as health_router
from app.controllers.subscriber_controller import router as subscriber_router
from app.controllers.webhook_controller import router as webhook_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(checkout_router)
api_router.include_router(subscriber_router)
api_router.include_router(webhook_router)
api_router.include_router(demo_router)
