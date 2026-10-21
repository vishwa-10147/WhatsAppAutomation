from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.workflows import router as workflows_router
from app.api.webhooks.whatsapp import router as whatsapp_webhook_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(whatsapp_router)
api_router.include_router(workflows_router)
api_router.include_router(whatsapp_webhook_router)