from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class WhatsAppMessage:
    to: str
    type: MessageType
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = None
    template_components: Optional[List[Dict[str, Any]]] = None
    interactive: Optional[Dict[str, Any]] = None


@dataclass
class SendResult:
    message_id: str
    status: MessageStatus
    error: Optional[str] = None


@dataclass
class IncomingMessage:
    id: str
    from_number: str
    timestamp: str
    type: MessageType
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_mime_type: Optional[str] = None
    media_sha256: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class StatusUpdate:
    message_id: str
    status: MessageStatus
    timestamp: str
    recipient_id: str
    conversation_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class WhatsAppProvider(ABC):
    @abstractmethod
    async def send_message(self, message: WhatsAppMessage) -> SendResult:
        pass

    @abstractmethod
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: List[Dict[str, Any]],
    ) -> SendResult:
        pass

    @abstractmethod
    async def upload_media(
        self,
        media_data: bytes,
        mime_type: str,
        filename: str,
    ) -> str:
        pass

    @abstractmethod
    async def get_media_url(self, media_id: str) -> str:
        pass

    @abstractmethod
    async def download_media(self, media_url: str) -> bytes:
        pass

    @abstractmethod
    async def verify_webhook(self, challenge: str, verify_token: str) -> Optional[str]:
        pass

    @abstractmethod
    async def parse_webhook(self, payload: Dict[str, Any]) -> List[IncomingMessage]:
        pass

    @abstractmethod
    async def parse_status_updates(self, payload: Dict[str, Any]) -> List[StatusUpdate]:
        pass