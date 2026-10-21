import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, OrganizationModel


class Contact(BaseModel):
    __tablename__ = "contacts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_opted_in: Mapped[bool] = mapped_column(default=True, nullable=False)
    opted_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opted_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[List["ContactTag"]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    custom_fields: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship()

    __table_args__ = (
        UniqueConstraint("organization_id", "phone_number", name="uq_org_phone_number"),
        Index("ix_contact_org_name", "organization_id", "name"),
        Index("ix_contact_org_last_interaction", "organization_id", "last_interaction_at"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, phone={self.phone_number})>"


class ContactTag(BaseModel):
    __tablename__ = "contact_tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    contact: Mapped["Contact"] = relationship(back_populates="tags")
    organization: Mapped["Organization"] = relationship()

    __table_args__ = (
        UniqueConstraint("organization_id", "contact_id", "name", name="uq_org_contact_tag"),
    )

    def __repr__(self) -> str:
        return f"<ContactTag(id={self.id}, name={self.name})>"


class Conversation(BaseModel):
    __tablename__ = "conversations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum("open", "pending", "resolved", name="conversation_status", native_enum=False),
        default="open",
        nullable=False,
    )
    unread_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)

    contact: Mapped["Contact"] = relationship()
    assignee: Mapped[Optional["User"]] = relationship()
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversation_org_status", "organization_id", "status"),
        Index("ix_conversation_org_last_message", "organization_id", "last_message_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, status={self.status})>"


class Message(BaseModel):
    __tablename__ = "messages"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    whatsapp_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("whatsapp_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    direction: Mapped[str] = mapped_column(
        SQLEnum("inbound", "outbound", name="message_direction", native_enum=False),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        SQLEnum("text", "image", "document", "audio", "video", "template", "interactive", name="message_type", native_enum=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    media_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    media_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    template_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    template_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("sent", "delivered", "read", "failed", name="message_status", native_enum=False),
        default="sent",
        nullable=False,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Optional["Conversation"]] = relationship(back_populates="messages")
    contact: Mapped[Optional["Contact"]] = relationship()

    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_org_external_id"),
        Index("ix_message_org_direction", "organization_id", "direction"),
        Index("ix_message_org_status", "organization_id", "status"),
        Index("ix_message_org_sent", "organization_id", "sent_at"),
        Index("ix_message_conversation", "conversation_id", "sent_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, type={self.type}, status={self.status})>"


class MessageTemplate(BaseModel):
    __tablename__ = "message_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en_US")
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    header_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    header_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    header_media_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    footer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buttons: Mapped[Optional[List[dict]]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("pending", "approved", "rejected", name="template_status", native_enum=False),
        default="pending",
        nullable=False,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejected_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship()

    __table_args__ = (
        UniqueConstraint("organization_id", "name", "language", name="uq_org_template_name_lang"),
    )

    def __repr__(self) -> str:
        return f"<MessageTemplate(id={self.id}, name={self.name}, status={self.status})>"