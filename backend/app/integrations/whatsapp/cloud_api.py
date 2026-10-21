import httpx
import json
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
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("whatsapp.cloud_api")


class WhatsAppCloudAPIError(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None, status_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class WhatsAppCloudAPIProvider(WhatsAppProvider):
    BASE_URL = "https://graph.facebook.com/v20.0"

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        business_account_id: str,
        webhook_verify_token: str,
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.business_account_id = business_account_id
        self.webhook_verify_token = webhook_verify_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _handle_error(self, response: httpx.Response) -> WhatsAppCloudAPIError:
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            message = error.get("message", "Unknown error")
            error_code = error.get("code")
            error_subcode = error.get("error_subcode")
            return WhatsAppCloudAPIError(
                message=f"{message} (code: {error_code}, subcode: {error_subcode})",
                error_code=str(error_code) if error_code else None,
                status_code=response.status_code,
            )
        except Exception:
            return WhatsAppCloudAPIError(
                message=f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

    async def send_message(self, message: WhatsAppMessage) -> SendResult:
        client = await self._get_client()
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"

        payload = self._build_message_payload(message)

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            message_id = result.get("messages", [{}])[0].get("id", "")
            return SendResult(message_id=message_id, status=MessageStatus.SENT)

        except httpx.HTTPStatusError as e:
            error = self._handle_error(e.response)
            logger.error(
                "whatsapp_send_failed",
                to=message.to,
                type=message.type.value,
                error=error.message,
                status_code=error.status_code,
            )
            return SendResult(message_id="", status=MessageStatus.FAILED, error=error.message)
        except Exception as e:
            logger.error("whatsapp_send_exception", error=str(e))
            return SendResult(message_id="", status=MessageStatus.FAILED, error=str(e))

    def _build_message_payload(self, message: WhatsAppMessage) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": message.to,
            "type": message.type.value,
        }

        if message.type == MessageType.TEXT:
            payload["text"] = {"body": message.text or ""}

        elif message.type in (MessageType.IMAGE, MessageType.DOCUMENT, MessageType.AUDIO, MessageType.VIDEO):
            media_type = message.type.value
            payload[media_type] = {}
            if message.media_id:
                payload[media_type]["id"] = message.media_id
            elif message.media_url:
                payload[media_type]["link"] = message.media_url
            if message.caption:
                payload[media_type]["caption"] = message.caption

        elif message.type == MessageType.TEMPLATE:
            payload["template"] = {
                "name": message.template_name,
                "language": {"code": message.template_language or "en_US"},
            }
            if message.template_components:
                payload["template"]["components"] = message.template_components

        elif message.type == MessageType.INTERACTIVE:
            payload["interactive"] = message.interactive

        return payload

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
        client = await self._get_client()
        url = f"{self.BASE_URL}/{self.phone_number_id}/media"

        files = {
            "file": (filename, media_data, mime_type),
            "messaging_product": (None, "whatsapp"),
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = await client.post(url, files=files, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("id", "")

        except httpx.HTTPStatusError as e:
            error = self._handle_error(e.response)
            logger.error("whatsapp_media_upload_failed", error=error.message)
            raise WhatsAppCloudAPIError(f"Media upload failed: {error.message}")

    async def get_media_url(self, media_id: str) -> str:
        client = await self._get_client()
        url = f"{self.BASE_URL}/{media_id}"

        try:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            return result.get("url", "")

        except httpx.HTTPStatusError as e:
            error = self._handle_error(e.response)
            logger.error("whatsapp_media_url_failed", media_id=media_id, error=error.message)
            raise WhatsAppCloudAPIError(f"Get media URL failed: {error.message}")

    async def download_media(self, media_url: str) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            response.raise_for_status()
            return response.content

    async def verify_webhook(self, challenge: str, verify_token: str) -> Optional[str]:
        if verify_token == self.webhook_verify_token:
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
                        id=msg.get("id", ""),
                        from_number=msg.get("from", ""),
                        timestamp=msg.get("timestamp", str(int(time.time()))),
                        type=MessageType(msg_type) if msg_type in [m.value for m in MessageType] else MessageType.TEXT,
                    )

                    if msg_type == "text":
                        incoming.text = msg.get("text", {}).get("body", "")
                    elif msg_type in ("image", "document", "audio", "video"):
                        media = msg.get(msg_type, {})
                        incoming.media_id = media.get("id")
                        incoming.media_mime_type = media.get("mime_type")
                        incoming.media_sha256 = media.get("sha256")
                        incoming.caption = media.get("caption")
                    elif msg_type == "interactive":
                        incoming.interactive = msg.get("interactive")

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