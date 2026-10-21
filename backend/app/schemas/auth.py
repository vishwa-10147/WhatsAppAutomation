from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserWithOrganizations(UserResponse):
    organizations: list["OrganizationResponse"] = []


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationMemberBase(BaseModel):
    user_id: UUID
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class OrganizationMemberCreate(OrganizationMemberBase):
    organization_id: UUID


class OrganizationMemberUpdate(BaseModel):
    role: Optional[str] = Field(default=None, pattern=r"^(admin|member|viewer)$")


class OrganizationMemberResponse(OrganizationMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user: UserResponse
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)
    organization_slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class RegisterResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
    token: Token


class SwitchOrganizationRequest(BaseModel):
    organization_id: UUID


class SwitchOrganizationResponse(BaseModel):
    token: Token
    organization: OrganizationResponse
