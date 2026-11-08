import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ResourceNotFoundError, ResourceValidationError
from app.core.events import AdminEventType, raise_event
from app.models import Plan, Subscription, Tenant
from app.schemas.subscriptions import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionStatus,
    SubscriptionUpdate,
)
from app.services.common import transaction


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        tenant_id: uuid.UUID | None = None,
        status: SubscriptionStatus | None = None,
    ) -> list[Subscription]:
        query = (
            select(Subscription)
            .order_by(Subscription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if tenant_id is not None:
            query = query.where(Subscription.tenant_id == tenant_id)
        if status is not None:
            query = query.where(Subscription.status == status)
        return list((await self.session.scalars(query)).all())

    async def get(self, subscription_id: uuid.UUID) -> Subscription:
        subscription = await self.session.get(Subscription, subscription_id)
        if subscription is None:
            raise ResourceNotFoundError("Subscription not found")
        return subscription

    async def create(self, payload: SubscriptionCreate) -> Subscription:
        async with transaction(self.session):
            await self._lock_tenant(payload.tenant_id)
            await self._lock_plan(payload.plan_id)
            subscription = Subscription(**payload.model_dump())
            self.session.add(subscription)
            await self.session.flush()
            await self.session.refresh(subscription)

        await raise_event(
            AdminEventType.SUBSCRIPTION_CREATED,
            "subscription",
            subscription.id,
            SubscriptionRead.model_validate(subscription).model_dump(mode="json"),
        )
        return subscription

    async def update(
        self,
        subscription_id: uuid.UUID,
        payload: SubscriptionUpdate,
    ) -> Subscription:
        async with transaction(self.session):
            changes = payload.model_dump(exclude_unset=True)
            if "plan_id" in changes:
                # Keep the plan-before-subscription lock order used by plan deletion.
                await self._lock_plan(changes["plan_id"])
            subscription = await self._get_for_update(subscription_id)
            period_start = changes.get(
                "current_period_start", subscription.current_period_start
            )
            period_end = changes.get("current_period_end", subscription.current_period_end)
            if period_end <= period_start:
                raise ResourceValidationError(
                    "current_period_end must be after current_period_start"
                )
            for field, value in changes.items():
                setattr(subscription, field, value)
            await self.session.flush()
            await self.session.refresh(subscription)

        await raise_event(
            AdminEventType.SUBSCRIPTION_UPDATED,
            "subscription",
            subscription.id,
            SubscriptionRead.model_validate(subscription).model_dump(mode="json"),
        )
        return subscription

    async def delete(self, subscription_id: uuid.UUID) -> None:
        async with transaction(self.session):
            subscription = await self._get_for_update(subscription_id)
            payload = SubscriptionRead.model_validate(subscription).model_dump(mode="json")
            await self.session.delete(subscription)
        await raise_event(
            AdminEventType.SUBSCRIPTION_DELETED,
            "subscription",
            subscription_id,
            payload,
        )

    async def _get_for_update(self, subscription_id: uuid.UUID) -> Subscription:
        subscription = await self.session.scalar(
            select(Subscription)
            .where(Subscription.id == subscription_id)
            .with_for_update()
        )
        if subscription is None:
            raise ResourceNotFoundError("Subscription not found")
        return subscription

    async def _lock_tenant(self, tenant_id: uuid.UUID) -> None:
        tenant_id_found = await self.session.scalar(
            select(Tenant.id).where(Tenant.id == tenant_id).with_for_update()
        )
        if tenant_id_found is None:
            raise ResourceNotFoundError("Tenant not found")

    async def _lock_plan(self, plan_id: uuid.UUID) -> None:
        plan_id_found = await self.session.scalar(
            select(Plan.id).where(Plan.id == plan_id).with_for_update()
        )
        if plan_id_found is None:
            raise ResourceNotFoundError("Plan not found")
