from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.plan import Plan
from app.schemas.plan import PlanCreate

class PlanService:
    @staticmethod
    async def create_plan(db: AsyncSession, payload: PlanCreate) -> Plan:
        stmt = select(Plan).where(Plan.slug == payload.slug).with_for_update()
        result = await db.execute(stmt)
        
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Plan slug already exists")

        plan = Plan(
            name=payload.name,
            slug=payload.slug,
            price_cents=payload.price_cents,
            currency=payload.currency,
            features=payload.features,
            is_active=True
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan