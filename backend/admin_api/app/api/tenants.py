from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services.tenant_service import TenantService
from launchpad_shared.auth import require_superuser

router = APIRouter(tags=["tenants"])

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_superuser)
):
    tenant = await TenantService.create_tenant(db, payload)
    return TenantResponse(
        id=str(tenant.id), name=tenant.name, slug=tenant.slug,
        status=tenant.status, is_active=tenant.is_active
    )