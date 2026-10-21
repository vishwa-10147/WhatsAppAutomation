from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Organization, OrganizationMember, User, UserRole
from app.schemas.auth import OrganizationCreate, OrganizationMemberCreate, UserCreate
from app.core.config import settings
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()
        return user


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        result = await self.session.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, org_data: OrganizationCreate) -> Organization:
        org = Organization(
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
        )
        self.session.add(org)
        await self.session.flush()
        return org

    async def get_user_organizations(self, user_id: UUID) -> list[Organization]:
        result = await self.session.execute(
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())


class OrganizationMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_org(self, user_id: UUID, org_id: UUID) -> Optional[OrganizationMember]:
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, member_data: OrganizationMemberCreate) -> OrganizationMember:
        member = OrganizationMember(
            user_id=member_data.user_id,
            organization_id=member_data.organization_id,
            role=member_data.role,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_user_membership(self, user_id: UUID, org_id: UUID) -> Optional[OrganizationMember]:
        return await self.get_by_user_and_org(user_id, org_id)

    async def is_admin(self, user_id: UUID, org_id: UUID) -> bool:
        member = await self.get_by_user_and_org(user_id, org_id)
        return member is not None and member.role == UserRole.ADMIN


class TokenRepository:
    def create_token(self, user_id: UUID, organization_id: UUID, expires_delta: timedelta | None = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_minutes)
        expires_at = datetime.now(timezone.utc) + expires_delta
        return jwt.encode(
            {"sub": str(user_id), "org": str(organization_id), "exp": expires_at},
            settings.app_secret_key,
            algorithm="HS256",
        )

    def validate_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
            user_id = UUID(payload["sub"])
            organization_id = UUID(payload["org"])
        except (JWTError, KeyError, ValueError, TypeError):
            return None
        return {"user_id": user_id, "organization_id": organization_id}


token_repository = TokenRepository()
