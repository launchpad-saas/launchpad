from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from launchpad_shared.schemas import BaseSchema
from launchpad_shared.auth import hash_password

router = APIRouter(tags=["internal"])

class InternalUserCreate(BaseSchema):
    tenant_id: str
    email: EmailStr
    password: str
    full_name: str

@router.post("/users", response_model=UserResponse)
async def create_tenant_admin(payload: InternalUserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        tenant_id=payload.tenant_id,
        is_superuser=False, # Tenant admins are not SaaS superusers
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