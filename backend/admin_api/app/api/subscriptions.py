import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.subscriptions import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionStatus,
    SubscriptionUpdate,
)
from app.services.subscriptions import SubscriptionService
from launchpad_shared.auth import require_superuser

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(require_superuser)],
)


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    tenant_id: uuid.UUID | None = None,
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await SubscriptionService(session).list(
        tenant_id=tenant_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    session: AsyncSession = Depends(get_db),
):
    return await SubscriptionService(session).create(payload)


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription(
    subscription_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    return await SubscriptionService(session).get(subscription_id)


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await SubscriptionService(session).update(subscription_id, payload)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    await SubscriptionService(session).delete(subscription_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
