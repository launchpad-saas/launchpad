import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ResourceNotFoundError
from app.core.events import AdminEventType, raise_event
from app.models import Plan
from app.schemas.plans import PlanCreate, PlanRead, PlanUpdate
from app.services.common import transaction


class PlanService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        active: bool | None = None,
    ) -> list[Plan]:
        query = select(Plan).order_by(Plan.created_at.desc()).offset(offset).limit(limit)
        if active is not None:
            query = query.where(Plan.is_active.is_(active))
        return list((await self.session.scalars(query)).all())

    async def get(self, plan_id: uuid.UUID) -> Plan:
        plan = await self.session.get(Plan, plan_id)
        if plan is None:
            raise ResourceNotFoundError("Plan not found")
        return plan

    async def create(self, payload: PlanCreate) -> Plan:
        async with transaction(self.session):
            plan = Plan(**payload.model_dump())
            self.session.add(plan)
            await self.session.flush()
            await self.session.refresh(plan)
        await raise_event(
            AdminEventType.PLAN_CREATED,
            "plan",
            plan.id,
            PlanRead.model_validate(plan).model_dump(mode="json"),
        )
        return plan

    async def update(self, plan_id: uuid.UUID, payload: PlanUpdate) -> Plan:
        async with transaction(self.session):
            plan = await self._get_for_update(plan_id)
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(plan, field, value)
            await self.session.flush()
            await self.session.refresh(plan)
        await raise_event(
            AdminEventType.PLAN_UPDATED,
            "plan",
            plan.id,
            PlanRead.model_validate(plan).model_dump(mode="json"),
        )
        return plan

    async def delete(self, plan_id: uuid.UUID) -> None:
        async with transaction(self.session):
            plan = await self._get_for_update(plan_id)
            payload = PlanRead.model_validate(plan).model_dump(mode="json")
            await self.session.delete(plan)
        await raise_event(AdminEventType.PLAN_DELETED, "plan", plan_id, payload)

    async def _get_for_update(self, plan_id: uuid.UUID) -> Plan:
        plan = await self.session.scalar(
            select(Plan).where(Plan.id == plan_id).with_for_update()
        )
        if plan is None:
            raise ResourceNotFoundError("Plan not found")
        return plan
