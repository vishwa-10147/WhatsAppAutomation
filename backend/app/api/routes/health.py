from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.db.session import get_session
from app.core.config import settings
from app.schemas.common import HealthResponse, ReadinessResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="alive",
        version="0.1.0",
        environment=settings.app_env,
        database="not_checked",
        redis="not_checked",
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(session: AsyncSession = Depends(get_session)):
    checks = {}
    ready = True

    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
        ready = False

    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        try:
            await r.ping()
        finally:
            await r.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
        ready = False

    if not ready:
        raise HTTPException(status_code=503, detail={"ready": False, "checks": checks})
    return ReadinessResponse(ready=ready, checks=checks)
