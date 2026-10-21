import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.whatsapp.base import (
    WhatsAppProvider,
    WhatsAppMessage,
    SendResult,
    IncomingMessage,
    StatusUpdate,
    MessageType,
    MessageStatus,
)
from app.integrations.whatsapp.factory import get_whatsapp_provider
from app.models.user import WhatsAppAccount
from app.models.message import Message, MessageTemplate
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("whatsapp.service")


class WhatsAppService:
    def __init__(self, session: AsyncSession, organization_id: UUID):
        self.session = session
        self.organization_id = organization_id
        self.provider: Optional[WhatsAppProvider] = None

    async def _get_provider(self) -> WhatsAppProvider:
        if self.provider is None:
            account = await self._get_default_account()
            if account and not settings.whatsapp_mock_mode:
                from app.integrations.whatsapp.factory import create_cloud_api_provider
                from app.core.security import credential_encryption

                access_token = credential_encryption.decrypt(account.access_token_encrypted)
                self.provider = create_cloud_api_provider(
                    access_token=access_token,
                    phone_number_id=account.phone_number_id,
                    business_account_id=account.business_account_id,
                    webhook_verify_token=account.webhook_verify_token,
                )
            else:
                self.provider = get_whatsapp_provider()
                if hasattr(self.provider, 'set_webhook_verify_token') and account:
                    self.provider.set_webhook_verify_token(account.webhook_verify_token)

        return self.provider

    async def _get_default_account(self) -> Optional[WhatsAppAccount]:
        result = await self.session.execute(
            select(WhatsAppAccount).where(
                and_(
                    WhatsAppAccount.organization_id == self.organization_id,
                    WhatsAppAccount.is_active == True,
                    WhatsAppAccount.is_default == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def send_text_message(
        self,
        to: str,
        text: str,
        account_id: Optional[UUID] = None,
    ) -> SendResult:
        message = WhatsAppMessage(to=to, type=MessageType.TEXT, text=text)
        return await self._send_with_retry(message, account_id)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: List[Dict[str, Any]],
        account_id: Optional[UUID] = None,
    ) -> SendResult:
        message = WhatsAppMessage(
            to=to,
            type=MessageType.TEMPLATE,
            template_name=template_name,
            template_language=language_code,
            template_components=components,
        )
        return await self._send_with_retry(message, account_id)

    async def send_media_message(
        self,
        to: str,
        media_type: MessageType,
        media_id: Optional[str] = None,
        media_url: Optional[str] = None,
        caption: Optional[str] = None,
        account_id: Optional[UUID] = None,
    ) -> SendResult:
        message = WhatsAppMessage(
            to=to,
            type=media_type,
            media_id=media_id,
            media_url=media_url,
            caption=caption,
        )
        return await self._send_with_retry(message, account_id)

    async def _send_with_retry(
        self,
        message: WhatsAppMessage,
        account_id: Optional[UUID] = None,
        max_retries: int = 3,
    ) -> SendResult:
        provider = await self._get_provider()

        for attempt in range(max_retries):
            result = await provider.send_message(message)

            if result.status != MessageStatus.FAILED:
                await self._persist_message(message, result, account_id)
                return result

            logger.warning(
                "whatsapp_send_retry",
                attempt=attempt + 1,
                max_retries=max_retries,
                error=result.error,
            )

            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        await self._persist_message(message, result, account_id)
        return result

    async def _persist_message(
        self,
        message: WhatsAppMessage,
        result: SendResult,
        account_id: Optional[UUID] = None,
    ):
        from app.models.message import Message

        db_message = Message(
            organization_id=self.organization_id,
            whatsapp_account_id=account_id,
            direction="outbound",
            type=message.type.value,
            content=message.text or message.caption or "",
            media_id=message.media_id,
            template_name=message.template_name,
            template_language=message.template_language,
            status=result.status.value,
            external_id=result.message_id,
            error_message=result.error,
            sent_at=datetime.now(timezone.utc),
        )
        self.session.add(db_message)
        await self.session.flush()

    async def process_incoming_messages(self, messages: List[IncomingMessage]):
        from app.models import Message, Contact, Conversation

        for msg in messages:
            contact = await self._get_or_create_contact(msg.from_number)

            conversation = await self._get_or_create_conversation(contact.id)

            db_message = Message(
                organization_id=self.organization_id,
                conversation_id=conversation.id,
                contact_id=contact.id,
                direction="inbound",
                type=msg.type.value,
                content=msg.text or msg.caption or "",
                media_id=msg.media_id,
                external_id=msg.id,
                status=MessageStatus.DELIVERED.value,
                received_at=datetime.fromtimestamp(int(msg.timestamp), tz=timezone.utc),
            )
            self.session.add(db_message)

            conversation.last_message_at = datetime.now(timezone.utc)
            conversation.unread_count = (conversation.unread_count or 0) + 1

            await self.session.flush()

        await self.session.commit()

    async def process_status_updates(self, updates: List[StatusUpdate]):
        from app.models import Message

        for update in updates:
            result = await self.session.execute(
                select(Message).where(
                    and_(
                        Message.organization_id == self.organization_id,
                        Message.external_id == update.message_id,
                    )
                )
            )
            message = result.scalar_one_or_none()

            if message:
                message.status = update.status.value
                message.updated_at = datetime.now(timezone.utc)

                if update.status == MessageStatus.FAILED and update.error_message:
                    message.error_message = update.error_message

                await self.session.flush()

        await self.session.commit()

    async def _get_or_create_contact(self, phone_number: str):
        from app.models import Contact

        result = await self.session.execute(
            select(Contact).where(
                and_(
                    Contact.organization_id == self.organization_id,
                    Contact.phone_number == phone_number,
                )
            )
        )
        contact = result.scalar_one_or_none()

        if not contact:
            contact = Contact(
                organization_id=self.organization_id,
                phone_number=phone_number,
                name=phone_number,
                is_opted_in=True,
            )
            self.session.add(contact)
            await self.session.flush()

        return contact

    async def _get_or_create_conversation(self, contact_id: UUID):
        from app.models import Conversation

        result = await self.session.execute(
            select(Conversation).where(
                and_(
                    Conversation.organization_id == self.organization_id,
                    Conversation.contact_id == contact_id,
                    Conversation.status == "open",
                )
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                organization_id=self.organization_id,
                contact_id=contact_id,
                status="open",
                unread_count=0,
            )
            self.session.add(conversation)
            await self.session.flush()

        return conversation

    async def upload_media(self, media_data: bytes, mime_type: str, filename: str) -> str:
        provider = await self._get_provider()
        return await provider.upload_media(media_data, mime_type, filename)

    async def get_media_url(self, media_id: str) -> str:
        provider = await self._get_provider()
        return await provider.get_media_url(media_id)

    async def download_media(self, media_url: str) -> bytes:
        provider = await self._get_provider()
        return await provider.download_media(media_url)