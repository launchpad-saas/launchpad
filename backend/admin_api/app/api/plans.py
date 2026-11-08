import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.plans import PlanCreate, PlanRead, PlanUpdate
from app.services.plans import PlanService
from launchpad_shared.auth import require_superuser

router = APIRouter(prefix="/plans", tags=["plans"], dependencies=[Depends(require_superuser)])


@router.get("", response_model=list[PlanRead])
async def list_plans(
    active: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await PlanService(session).list(offset=offset, limit=limit, active=active)


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(payload: PlanCreate, session: AsyncSession = Depends(get_db)):
    return await PlanService(session).create(payload)


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan(plan_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    return await PlanService(session).get(plan_id)


@router.patch("/{plan_id}", response_model=PlanRead)
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await PlanService(session).update(plan_id, payload)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    await PlanService(session).delete(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
