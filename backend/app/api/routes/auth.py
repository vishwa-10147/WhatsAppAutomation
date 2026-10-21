from fastapi import APIRouter, Cookie, Depends, HTTPException, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.auth import (
    LoginRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
    RegisterRequest,
    RegisterResponse,
    SwitchOrganizationRequest,
    SwitchOrganizationResponse,
    Token,
    UserResponse,
    UserWithOrganizations,
)
from app.services.auth import AuthService
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    access_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> tuple:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("origin") not in settings.cors_origins:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request origin is not allowed")
        token = access_token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return await auth_service.get_current_user(token)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
        path="/api/v1",
    )


async def get_current_user_id(
    current_user: tuple = Depends(get_current_user),
) -> str:
    user, org_id = current_user
    return str(user.id)


async def get_current_org_id(
    current_user: tuple = Depends(get_current_user),
) -> str:
    user, org_id = current_user
    return str(org_id)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.register(data)
    set_session_cookie(response, result.token.access_token)
    return result


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = await auth_service.login(data)
    set_session_cookie(response, result.access_token)
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    _current_user: tuple = Depends(get_current_user),
):
    response.delete_cookie(
        key="access_token",
        path="/api/v1",
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserWithOrganizations)
async def get_me(
    current_user: tuple = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    user, _ = current_user
    return await auth_service.get_user_with_orgs(user)


@router.post("/switch-organization", response_model=SwitchOrganizationResponse)
async def switch_organization(
    data: SwitchOrganizationRequest,
    response: Response,
    current_user: tuple = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    user, _ = current_user
    result = await auth_service.switch_organization(user, data)
    set_session_cookie(response, result.token.access_token)
    return result


@router.get("/organizations/{org_id}/members", response_model=list[OrganizationMemberResponse])
async def get_organization_members(
    org_id: str,
    current_user: tuple = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    user, _ = current_user
    from uuid import UUID
    return await auth_service.get_organization_members(UUID(org_id), user.id)
