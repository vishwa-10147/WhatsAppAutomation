from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.api.routes.auth import get_current_org_id
from app.models.user import WhatsAppAccount
from app.models.message import MessageTemplate, Contact
from app.services.whatsapp import WhatsAppService
from app.core.security import credential_encryption
from app.integrations.whatsapp.factory import create_cloud_api_provider
from app.integrations.whatsapp.base import MessageType
from app.core.logging import get_logger

logger = get_logger("whatsapp.api")

router = APIRouter(prefix="/accounts", tags=["whatsapp-accounts"])


class WhatsAppAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number_id: str = Field(..., min_length=1, max_length=100)
    business_account_id: str = Field(..., min_length=1, max_length=100)
    access_token: str = Field(..., min_length=1)
    webhook_verify_token: str = Field(..., min_length=1, max_length=255)
    is_default: bool = False


class WhatsAppAccountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class WhatsAppAccountResponse(BaseModel):
    id: UUID
    name: str
    phone_number_id: str
    business_account_id: str
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SendTextRequest(BaseModel):
    to: str = Field(..., pattern=r"^\+\d{10,15}$")
    text: str = Field(..., min_length=1, max_length=4096)
    account_id: Optional[UUID] = None


class SendTemplateRequest(BaseModel):
    to: str = Field(..., pattern=r"^\+\d{10,15}$")
    template_name: str
    language_code: str = "en_US"
    components: Optional[List[dict]] = None
    account_id: Optional[UUID] = None


class SendMediaRequest(BaseModel):
    to: str = Field(..., pattern=r"^\+\d{10,15}$")
    media_type: str = Field(..., pattern=r"^(image|document|audio|video)$")
    media_id: Optional[str] = None
    caption: Optional[str] = None
    account_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    message_id: str
    status: str
    error: Optional[str] = None


@router.post("", response_model=WhatsAppAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_whatsapp_account(
    data: WhatsAppAccountCreate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    existing = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.organization_id == UUID(org_id),
                WhatsAppAccount.phone_number_id == data.phone_number_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number ID already registered")

    if data.is_default:
        await session.execute(
            select(WhatsAppAccount).where(
                and_(
                    WhatsAppAccount.organization_id == UUID(org_id),
                    WhatsAppAccount.is_default == True,
                )
            )
        )
        for acc in (await session.execute(
            select(WhatsAppAccount).where(
                and_(
                    WhatsAppAccount.organization_id == UUID(org_id),
                    WhatsAppAccount.is_default == True,
                )
            )
        )).scalars().all():
            acc.is_default = False

    account = WhatsAppAccount(
        organization_id=UUID(org_id),
        name=data.name,
        phone_number_id=data.phone_number_id,
        business_account_id=data.business_account_id,
        access_token_encrypted=credential_encryption.encrypt(data.access_token),
        webhook_verify_token=data.webhook_verify_token,
        is_default=data.is_default,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    logger.info("whatsapp_account_created", account_id=str(account.id), org_id=org_id)

    return WhatsAppAccountResponse(
        id=account.id,
        name=account.name,
        phone_number_id=account.phone_number_id,
        business_account_id=account.business_account_id,
        is_active=account.is_active,
        is_default=account.is_default,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
    )


@router.get("", response_model=List[WhatsAppAccountResponse])
async def list_whatsapp_accounts(
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(WhatsAppAccount.organization_id == UUID(org_id))
    )
    accounts = result.scalars().all()

    return [
        WhatsAppAccountResponse(
            id=acc.id,
            name=acc.name,
            phone_number_id=acc.phone_number_id,
            business_account_id=acc.business_account_id,
            is_active=acc.is_active,
            is_default=acc.is_default,
            created_at=acc.created_at.isoformat(),
            updated_at=acc.updated_at.isoformat(),
        )
        for acc in accounts
    ]


@router.get("/{account_id}", response_model=WhatsAppAccountResponse)
async def get_whatsapp_account(
    account_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    return WhatsAppAccountResponse(
        id=account.id,
        name=account.name,
        phone_number_id=account.phone_number_id,
        business_account_id=account.business_account_id,
        is_active=account.is_active,
        is_default=account.is_default,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
    )


@router.patch("/{account_id}", response_model=WhatsAppAccountResponse)
async def update_whatsapp_account(
    account_id: UUID,
    data: WhatsAppAccountUpdate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    if data.name is not None:
        account.name = data.name
    if data.is_active is not None:
        account.is_active = data.is_active
    if data.is_default is not None:
        if data.is_default and not account.is_default:
            await session.execute(
                select(WhatsAppAccount).where(
                    and_(
                        WhatsAppAccount.organization_id == UUID(org_id),
                        WhatsAppAccount.is_default == True,
                    )
                )
            )
            for acc in (await session.execute(
                select(WhatsAppAccount).where(
                    and_(
                        WhatsAppAccount.organization_id == UUID(org_id),
                        WhatsAppAccount.is_default == True,
                    )
                )
            )).scalars().all():
                acc.is_default = False
        account.is_default = data.is_default

    await session.commit()
    await session.refresh(account)

    return WhatsAppAccountResponse(
        id=account.id,
        name=account.name,
        phone_number_id=account.phone_number_id,
        business_account_id=account.business_account_id,
        is_active=account.is_active,
        is_default=account.is_default,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whatsapp_account(
    account_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    await session.delete(account)
    await session.commit()


@router.post("/{account_id}/send/text", response_model=MessageResponse)
async def send_text_message(
    account_id: UUID,
    data: SendTextRequest,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    service = WhatsAppService(session, UUID(org_id))
    result = await service.send_text_message(data.to, data.text, account_id)

    return MessageResponse(
        message_id=result.message_id,
        status=result.status.value,
        error=result.error,
    )


@router.post("/{account_id}/send/template", response_model=MessageResponse)
async def send_template_message(
    account_id: UUID,
    data: SendTemplateRequest,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    service = WhatsAppService(session, UUID(org_id))
    result = await service.send_template_message(
        data.to,
        data.template_name,
        data.language_code,
        data.components or [],
        account_id,
    )

    return MessageResponse(
        message_id=result.message_id,
        status=result.status.value,
        error=result.error,
    )


@router.post("/{account_id}/send/media", response_model=MessageResponse)
async def send_media_message(
    account_id: UUID,
    data: SendMediaRequest,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    media_type_map = {
        "image": MessageType.IMAGE,
        "document": MessageType.DOCUMENT,
        "audio": MessageType.AUDIO,
        "video": MessageType.VIDEO,
    }

    service = WhatsAppService(session, UUID(org_id))
    result = await service.send_media_message(
        data.to,
        media_type_map[data.media_type],
        media_id=data.media_id,
        caption=data.caption,
        account_id=account_id,
    )

    return MessageResponse(
        message_id=result.message_id,
        status=result.status.value,
        error=result.error,
    )


@router.post("/{account_id}/upload-media")
async def upload_media(
    account_id: UUID,
    file: UploadFile = File(...),
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WhatsAppAccount).where(
            and_(
                WhatsAppAccount.id == account_id,
                WhatsAppAccount.organization_id == UUID(org_id),
            )
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="WhatsApp account not found")

    media_data = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    filename = file.filename or "media"

    service = WhatsAppService(session, UUID(org_id))
    media_id = await service.upload_media(media_data, mime_type, filename)

    return {"media_id": media_id}