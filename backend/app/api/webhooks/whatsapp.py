from fastapi import APIRouter, Request, Depends, HTTPException, Query, Header
from fastapi.responses import PlainTextResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.integrations.whatsapp.factory import get_whatsapp_provider
from app.services.whatsapp import WhatsAppService
from app.core.config import settings
from app.core.logging import get_logger
from app.api.routes.auth import get_current_org_id
from app.models.user import WhatsAppAccount

logger = get_logger("whatsapp.webhook")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_mode != "subscribe":
        raise HTTPException(status_code=403, detail="Invalid mode")

    provider = get_whatsapp_provider()
    challenge = await provider.verify_webhook(hub_challenge, hub_verify_token)

    if challenge is None:
        logger.warning("whatsapp_webhook_verification_failed", token=hub_verify_token)
        raise HTTPException(status_code=403, detail="Invalid verify token")

    logger.info("whatsapp_webhook_verified")
    return PlainTextResponse(content=challenge)


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    payload = await request.json()

    logger.info("whatsapp_webhook_received", payload_keys=list(payload.keys()))

    if not settings.whatsapp_mock_mode and x_hub_signature_256:
        if not _verify_signature(payload, x_hub_signature_256):
            logger.warning("whatsapp_webhook_invalid_signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        provider = get_whatsapp_provider()

        phone_number_id = _get_org_id_from_payload(payload)
        if not phone_number_id:
            logger.warning("whatsapp_webhook_missing_phone_number_id")
            return {"status": "ok"}

        org_id_str = await _resolve_org_id(session, phone_number_id)
        if not org_id_str:
            logger.warning("whatsapp_webhook_unknown_phone_number", phone_number_id=phone_number_id)
            return {"status": "ok"}

        from uuid import UUID
        org_id = UUID(org_id_str)
        service = WhatsAppService(session, org_id)

        messages = await provider.parse_webhook(payload)
        if messages:
            await service.process_incoming_messages(messages)

        status_updates = await provider.parse_status_updates(payload)
        if status_updates:
            await service.process_status_updates(status_updates)

        return {"status": "ok"}

    except Exception as e:
        logger.error("whatsapp_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")


def _verify_signature(payload: dict, signature: str) -> bool:
    import hmac
    import hashlib

    app_secret = settings.whatsapp_app_secret
    if not app_secret:
        return True

    expected = hmac.new(
        app_secret.encode(),
        json.dumps(payload, separators=(",", ":")).encode(),
        hashlib.sha256,
    ).hexdigest()

    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)


def _get_org_id_from_payload(payload: dict) -> Optional[str]:
    try:
        entry = payload.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id")
                if phone_number_id:
                    return phone_number_id
    except Exception:
        pass
    return None


async def _resolve_org_id(session: AsyncSession, phone_number_id: str) -> Optional[str]:
    result = await session.execute(
        select(WhatsAppAccount.organization_id).where(
            WhatsAppAccount.phone_number_id == phone_number_id
        )
    )
    org_id = result.scalar_one_or_none()
    return str(org_id) if org_id else None