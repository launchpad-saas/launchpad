import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    AuthTokens,
    Message,
    PasswordChange,
    PasswordReset,
    TokenAction,
    TokenRefresh,
    UserCreate,
    UserList,
    UserRead,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)
from app.services.auth import AuthService
from app.services.users import UserService
from launchpad_shared.auth import AuthClaims, require_superuser

router = APIRouter(tags=["authentication"])


@router.post("/login/access-token", response_model=AuthTokens)
async def login_access_token(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    tenant_id = getattr(request.state, "tenant_id", None)
    return await AuthService(session).login(
        email=form.username,
        password=form.password,
        tenant_id=tenant_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/login/refresh", response_model=AuthTokens)
async def refresh_tokens(
    payload: TokenRefresh,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await AuthService(session).refresh(
        payload.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/login/logout", response_model=Message)
async def logout(
    payload: TokenRefresh | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).logout(
        user.id,
        payload.refresh_token if payload else None,
    )
    return Message(message="Logged out")


@router.post("/login/logout-all", response_model=Message)
async def logout_all(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).logout(user.id)
    return Message(message="Logged out from all sessions")


@router.post("/login/test-token", response_model=UserRead)
async def test_token(user: User = Depends(get_current_user)):
    return user


@router.post("/users/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegister,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    tenant_id = getattr(request.state, "tenant_id", None)
    return await AuthService(session).register(payload, tenant_id)


@router.post("/verify-email", response_model=UserRead)
async def verify_email(
    payload: TokenAction,
    session: AsyncSession = Depends(get_db),
):
    return await AuthService(session).verify_email(payload.token)


@router.post("/resend-verification", response_model=Message)
async def resend_verification(
    request: Request,
    email: str = Query(min_length=3, max_length=255),
    session: AsyncSession = Depends(get_db),
):
    tenant_id = getattr(request.state, "tenant_id", None)
    await AuthService(session).resend_verification(email, tenant_id)
    return Message(message="If the account requires verification, an email will be sent")


@router.post("/password-recovery/{email}", response_model=Message)
async def password_recovery_legacy(
    email: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).request_password_reset(
        email,
        getattr(request.state, "tenant_id", None),
    )
    return Message(message="If the account exists, password reset instructions will be sent")


@router.post("/password-recovery", response_model=Message)
async def password_recovery(
    request: Request,
    email: str = Query(min_length=3, max_length=255),
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).request_password_reset(
        email,
        getattr(request.state, "tenant_id", None),
    )
    return Message(message="If the account exists, password reset instructions will be sent")


@router.post("/reset-password/", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: PasswordReset,
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).reset_password(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/me", response_model=UserRead)
async def read_user_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/users/me", response_model=UserRead)
async def update_user_me(
    payload: UserUpdateMe,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await AuthService(session).update_profile(user.id, payload)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await UserService(session).delete(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/users/me/password", response_model=Message)
async def update_password_me(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await AuthService(session).change_password(user.id, payload)
    return Message(message="Password updated; please sign in again")


@router.get("/users/", response_model=UserList)
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _: AuthClaims = Depends(require_superuser),
    session: AsyncSession = Depends(get_db),
):
    users, total = await UserService(session).list(offset=offset, limit=limit)
    return UserList(data=users, count=total)


@router.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: AuthClaims = Depends(require_superuser),
    session: AsyncSession = Depends(get_db),
):
    return await UserService(session).create(payload)


@router.get("/users/{user_id}", response_model=UserRead)
async def read_user_by_id(
    user_id: uuid.UUID,
    _: AuthClaims = Depends(require_superuser),
    session: AsyncSession = Depends(get_db),
):
    return await UserService(session).get(user_id)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _: AuthClaims = Depends(require_superuser),
    session: AsyncSession = Depends(get_db),
):
    return await UserService(session).update(user_id, payload)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    _: AuthClaims = Depends(require_superuser),
    session: AsyncSession = Depends(get_db),
):
    await UserService(session).delete(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
