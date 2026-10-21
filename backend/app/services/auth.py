from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auth import (
    OrganizationMemberRepository,
    OrganizationRepository,
    TokenRepository,
    UserRepository,
    token_repository,
)
from app.schemas.auth import (
    LoginRequest,
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    RegisterRequest,
    RegisterResponse,
    SwitchOrganizationRequest,
    SwitchOrganizationResponse,
    Token,
    UserCreate,
    UserResponse,
    UserWithOrganizations,
)
from app.core.security import verify_password
from app.core.config import settings
from app.models.user import UserRole, User


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.member_repo = OrganizationMemberRepository(session)
        self.token_repo = token_repository

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        existing_org = await self.org_repo.get_by_slug(data.organization_slug)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already taken",
            )

        user = await self.user_repo.create(UserCreate(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
        ))

        org = await self.org_repo.create(OrganizationCreate(
            name=data.organization_name,
            slug=data.organization_slug,
        ))

        await self.member_repo.create(OrganizationMemberCreate(
            user_id=user.id,
            organization_id=org.id,
            role=UserRole.ADMIN,
        ))

        token = self.token_repo.create_token(user.id, org.id)

        return RegisterResponse(
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(org),
            token=Token(access_token=token, expires_in=settings.access_token_minutes * 60),
        )

    async def login(self, data: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        organizations = await self.org_repo.get_user_organizations(user.id)
        if not organizations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no organization access",
            )

        default_org = organizations[0]
        await self.user_repo.update_last_login(user)

        token = self.token_repo.create_token(user.id, default_org.id)

        return Token(access_token=token, expires_in=settings.access_token_minutes * 60)

    async def get_current_user(self, token: str) -> tuple[User, UUID]:
        token_data = self.token_repo.validate_token(token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        user = await self.user_repo.get_by_id(token_data["user_id"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        membership = await self.member_repo.get_user_membership(user.id, token_data["organization_id"])
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization access has been revoked",
            )
        org = await self.org_repo.get_by_id(token_data["organization_id"])
        if org is None or not org.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization is unavailable")

        return user, token_data["organization_id"]

    async def switch_organization(self, user: User, data: SwitchOrganizationRequest) -> SwitchOrganizationResponse:
        membership = await self.member_repo.get_user_membership(user.id, data.organization_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization",
            )

        org = await self.org_repo.get_by_id(data.organization_id)
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or inactive",
            )

        token = self.token_repo.create_token(user.id, org.id)

        return SwitchOrganizationResponse(
            token=Token(access_token=token, expires_in=settings.access_token_minutes * 60),
            organization=OrganizationResponse.model_validate(org),
        )

    async def get_user_with_orgs(self, user: User) -> UserWithOrganizations:
        organizations = await self.org_repo.get_user_organizations(user.id)
        return UserWithOrganizations(
            **UserResponse.model_validate(user).model_dump(),
            organizations=[OrganizationResponse.model_validate(org) for org in organizations],
        )

    async def get_organization_members(self, org_id: UUID, current_user_id: UUID) -> list[OrganizationMemberResponse]:
        if not await self.member_repo.is_admin(current_user_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view organization members",
            )

        from sqlalchemy import select
        from app.models.user import OrganizationMember, User as UserModel

        result = await self.user_repo.session.execute(
            select(OrganizationMember, UserModel)
            .join(UserModel, OrganizationMember.user_id == UserModel.id)
            .where(OrganizationMember.organization_id == org_id)
        )
        members = []
        for member, user_obj in result.all():
            members.append(OrganizationMemberResponse(
                id=member.id,
                user_id=member.user_id,
                organization_id=member.organization_id,
                role=member.role,
                user=UserResponse.model_validate(user_obj),
                created_at=member.created_at,
                updated_at=member.updated_at,
            ))
        return members
