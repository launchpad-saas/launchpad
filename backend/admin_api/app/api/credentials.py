import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.credentials import (
    CredentialCreate,
    CredentialCreated,
    CredentialRead,
    CredentialUpdate,
)
from app.services.credentials import CredentialService
from launchpad_shared.auth import require_superuser

router = APIRouter(
    tags=["client credentials"],
    dependencies=[Depends(require_superuser)],
)


@router.get(
    "/tenants/{tenant_id}/credentials",
    response_model=list[CredentialRead],
)
async def list_credentials(
    tenant_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await CredentialService(session).list_for_tenant(
        tenant_id,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/tenants/{tenant_id}/credentials",
    response_model=CredentialCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    tenant_id: uuid.UUID,
    payload: CredentialCreate,
    session: AsyncSession = Depends(get_db),
):
    return await CredentialService(session).create(tenant_id, payload)


@router.patch("/credentials/{credential_id}", response_model=CredentialRead)
async def update_credential(
    credential_id: uuid.UUID,
    payload: CredentialUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await CredentialService(session).update(credential_id, payload)


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_credential(
    credential_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    await CredentialService(session).revoke(credential_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
