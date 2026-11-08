import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tenants import TenantCreate, TenantRead, TenantStatus, TenantUpdate
from app.services.tenants import TenantService
from launchpad_shared.auth import require_superuser

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(require_superuser)],
)


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    status_filter: TenantStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    session: AsyncSession = Depends(get_db),
):
    return await TenantService(session).list(
        offset=offset,
        limit=limit,
        status=status_filter,
        search=search,
    )


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    session: AsyncSession = Depends(get_db),
):
    return await TenantService(session).create(payload)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(tenant_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    return await TenantService(session).get(tenant_id)


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await TenantService(session).update(tenant_id, payload)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    await TenantService(session).delete(tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
