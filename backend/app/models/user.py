import uuid
from datetime import datetime, timezone
from typing import Optional, List
import enum

from sqlalchemy import String, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, OrganizationModel


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[List["OrganizationMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    members: Mapped[List["OrganizationMember"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    whatsapp_accounts: Mapped[List["WhatsAppAccount"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"


class OrganizationMember(BaseModel):
    __tablename__ = "organization_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.MEMBER,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="memberships")
    organization: Mapped["Organization"] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
        Index("ix_org_member_org_id", "organization_id"),
        Index("ix_org_member_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationMember(user_id={self.user_id}, org_id={self.organization_id}, role={self.role})>"


class WhatsAppAccount(OrganizationModel):
    __tablename__ = "whatsapp_accounts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    business_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_verify_token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="whatsapp_accounts")

    __table_args__ = (
        UniqueConstraint("organization_id", "phone_number_id", name="uq_org_phone_number"),
        Index("ix_wa_account_org_active", "organization_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<WhatsAppAccount(id={self.id}, phone_number_id={self.phone_number_id})>"