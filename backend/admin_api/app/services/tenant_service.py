from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate

class TenantService:
    @staticmethod
    async def create_tenant(db: AsyncSession, payload: TenantCreate) -> Tenant:
        # Lock check (prevents race conditions if two requests try same slug)
        stmt = select(Tenant).where(Tenant.slug == payload.slug).with_for_update()
        result = await db.execute(stmt)
        
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Tenant slug already exists"
            )

        tenant = Tenant(
            name=payload.name,
            slug=payload.slug,
            legal_business_name=payload.legal_business_name,
            gstin=payload.gstin,
            support_email=payload.support_email,
            status="active",
            is_active=True
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant