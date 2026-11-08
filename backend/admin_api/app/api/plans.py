from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.plan import PlanCreate, PlanResponse
from app.services.plan_service import PlanService
from launchpad_shared.auth import require_superuser

router = APIRouter(tags=["plans"])

@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_superuser)
):
    plan = await PlanService.create_plan(db, payload)
    return PlanResponse(
        id=str(plan.id), name=plan.name, slug=plan.slug,
        price_cents=plan.price_cents, currency=plan.currency,
        is_active=plan.is_active
    )