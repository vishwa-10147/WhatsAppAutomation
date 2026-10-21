import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.integrations.whatsapp.base import (
    WhatsAppProvider,
    WhatsAppMessage,
    SendResult,
    IncomingMessage,
    StatusUpdate,
    MessageType,
    MessageStatus,
)


class MockWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self._sent_messages: List[WhatsAppMessage] = []
        self._media_store: Dict[str, bytes] = {}
        self._webhook_verify_token: Optional[str] = None
        self._message_statuses: Dict[str, MessageStatus] = {}

    def set_webhook_verify_token(self, token: str):
        self._webhook_verify_token = token

    async def send_message(self, message: WhatsAppMessage) -> SendResult:
        message_id = f"wamid.mock_{uuid.uuid4().hex[:16]}"
        self._sent_messages.append(message)
        self._message_statuses[message_id] = MessageStatus.SENT

        # Simulate async delivery
        import asyncio
        asyncio.create_task(self._simulate_delivery(message_id))

        return SendResult(message_id=message_id, status=MessageStatus.SENT)

    async def _simulate_delivery(self, message_id: str):
        import asyncio
        await asyncio.sleep(0.5)
        self._message_statuses[message_id] = MessageStatus.DELIVERED
        await asyncio.sleep(0.5)
        self._message_statuses[message_id] = MessageStatus.READ

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: List[Dict[str, Any]],
    ) -> SendResult:
        message = WhatsAppMessage(
            to=to,
            type=MessageType.TEMPLATE,
            template_name=template_name,
            template_language=language_code,
            template_components=components,
        )
        return await self.send_message(message)

    async def upload_media(
        self,
        media_data: bytes,
        mime_type: str,
        filename: str,
    ) -> str:
        media_id = f"mock_media_{uuid.uuid4().hex[:16]}"
        self._media_store[media_id] = media_data
        return media_id

    async def get_media_url(self, media_id: str) -> str:
        return f"https://mock-whatsapp.example.com/media/{media_id}"

    async def download_media(self, media_url: str) -> bytes:
        media_id = media_url.split("/")[-1]
        return self._media_store.get(media_id, b"")

    async def verify_webhook(self, challenge: str, verify_token: str) -> Optional[str]:
        if self._webhook_verify_token and verify_token == self._webhook_verify_token:
            return challenge
        return None

    async def parse_webhook(self, payload: Dict[str, Any]) -> List[IncomingMessage]:
        messages = []

        entry = payload.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages_data = value.get("messages", [])
                for msg in messages_data:
                    msg_type = msg.get("type", "text")
                    incoming = IncomingMessage(
                        id=msg.get("id", f"mock_{uuid.uuid4().hex[:16]}"),
                        from_number=msg.get("from", ""),
                        timestamp=msg.get("timestamp", str(int(time.time()))),
                        type=MessageType(msg_type) if msg_type in MessageType.__members__.values() else MessageType.TEXT,
                    )

                    if msg_type == "text":
                        incoming.text = msg.get("text", {}).get("body", "")
                    elif msg_type in ("image", "document", "audio", "video"):
                        media = msg.get(msg_type, {})
                        incoming.media_id = media.get("id")
                        incoming.media_mime_type = media.get("mime_type")
                        incoming.media_sha256 = media.get("sha256")
                        incoming.caption = media.get("caption")

                    if "context" in msg:
                        incoming.context = msg["context"]

                    messages.append(incoming)

        return messages

    async def parse_status_updates(self, payload: Dict[str, Any]) -> List[StatusUpdate]:
        updates = []

        entry = payload.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                statuses = value.get("statuses", [])
                for status in statuses:
                    updates.append(StatusUpdate(
                        message_id=status.get("id", ""),
                        status=MessageStatus(status.get("status", "sent")),
                        timestamp=status.get("timestamp", str(int(time.time()))),
                        recipient_id=status.get("recipient_id", ""),
                        conversation_id=status.get("conversation", {}).get("id") if "conversation" in status else None,
                        error_code=status.get("errors", [{}])[0].get("code") if status.get("errors") else None,
                        error_message=status.get("errors", [{}])[0].get("title") if status.get("errors") else None,
                    ))

        return updates

    def get_sent_messages(self) -> List[WhatsAppMessage]:
        return self._sent_messages.copy()

    def clear_sent_messages(self):
        self._sent_messages.clear()
        self._message_statuses.clear()