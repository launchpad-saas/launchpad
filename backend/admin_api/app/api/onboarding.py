from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.onboarding import TenantRegistrationRequest, TenantRegistrationResponse
from app.services.onboarding import OnboardingService

router = APIRouter(tags=["onboarding"])

@router.post("/register", response_model=TenantRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_new_tenant(
    payload: TenantRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint for new clients to sign up.
    Creates Tenant, Subscription, and Client Credentials atomically.
    """
    return await OnboardingService.register_tenant(db, payload)