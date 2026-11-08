import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ResourceNotFoundError
from app.core.events import AdminEventType, raise_event
from app.models import Tenant
from app.schemas.tenants import TenantCreate, TenantRead, TenantStatus, TenantUpdate
from app.services.common import transaction


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        status: TenantStatus | None = None,
        search: str | None = None,
    ) -> list[Tenant]:
        query = select(Tenant).order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
        if status is not None:
            query = query.where(Tenant.status == status)
        if search is not None:
            query = query.where(Tenant.name.ilike(f"%{search}%"))
        return list((await self.session.scalars(query)).all())

    async def get(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise ResourceNotFoundError("Tenant not found")
        return tenant

    async def create(self, payload: TenantCreate) -> Tenant:
        async with transaction(self.session):
            tenant = Tenant(**payload.model_dump())
            self.session.add(tenant)
            await self.session.flush()
            await self.session.refresh(tenant)
        await raise_event(
            AdminEventType.TENANT_CREATED,
            "tenant",
            tenant.id,
            TenantRead.model_validate(tenant).model_dump(mode="json"),
        )
        return tenant

    async def update(self, tenant_id: uuid.UUID, payload: TenantUpdate) -> Tenant:
        async with transaction(self.session):
            tenant = await self._get_for_update(tenant_id)
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(tenant, field, value)
            await self.session.flush()
            await self.session.refresh(tenant)
        await raise_event(
            AdminEventType.TENANT_UPDATED,
            "tenant",
            tenant.id,
            TenantRead.model_validate(tenant).model_dump(mode="json"),
        )
        return tenant

    async def delete(self, tenant_id: uuid.UUID) -> None:
        async with transaction(self.session):
            tenant = await self._get_for_update(tenant_id)
            payload = TenantRead.model_validate(tenant).model_dump(mode="json")
            await self.session.delete(tenant)
        await raise_event(AdminEventType.TENANT_DELETED, "tenant", tenant_id, payload)

    async def _get_for_update(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.session.scalar(
            select(Tenant).where(Tenant.id == tenant_id).with_for_update()
        )
        if tenant is None:
            raise ResourceNotFoundError("Tenant not found")
        return tenant
