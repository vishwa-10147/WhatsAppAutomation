from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import configure_logging, RequestLoggingMiddleware
from app.db.session import close_db, init_db
from app.integrations.whatsapp.factory import get_whatsapp_provider
from app.integrations.whatsapp.mock_provider import MockWhatsAppProvider

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    
    # Initialize mock provider with webhook verify token from default account
    if settings.whatsapp_mock_mode:
        from app.db.session import async_session_maker
        from app.models.user import WhatsAppAccount
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(WhatsAppAccount).where(
                    WhatsAppAccount.is_default == True,
                    WhatsAppAccount.is_active == True,
                ).limit(1)
            )
            account = result.scalar_one_or_none()
            if account:
                provider = get_whatsapp_provider()
                if isinstance(provider, MockWhatsAppProvider):
                    provider.set_webhook_verify_token(account.webhook_verify_token)
    
    yield
    await close_db()


app = FastAPI(
    title="WhatsApp Automation Platform",
    description="A multi-tenant WhatsApp Business automation platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "WhatsApp Automation Platform",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
