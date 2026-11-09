from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from launchpad_shared.auth import hash_password, verify_password, create_access_token, require_auth, AuthClaims

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        tenant_id=payload.tenant_id,
        is_superuser=payload.tenant_id is None,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        is_superuser=user.is_superuser, is_active=user.is_active
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=user.tenant_id,
        roles=["admin"] if user.is_superuser else ["user"],
        extra_claims={"is_superuser": user.is_superuser}
    )
    return TokenResponse(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_me(claims: AuthClaims = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == uuid.UUID(claims.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        is_superuser=user.is_superuser, is_active=user.is_active
    )