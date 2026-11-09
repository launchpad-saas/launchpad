import uuid
import secrets
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.client_credential import ClientCredential
from app.schemas.onboarding import TenantRegistrationRequest, TenantRegistrationResponse
from app.services.provisioning import ProvisioningService
from launchpad_shared.auth import hash_password

class OnboardingService:
    @staticmethod
    async def register_tenant(db: AsyncSession, payload: TenantRegistrationRequest) -> TenantRegistrationResponse:
        # 1. Lock and check if slug exists
        stmt = select(Tenant).where(Tenant.slug == payload.slug).with_for_update()
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Slug already taken")

        # 2. Fetch the default 'Free' plan
        plan_stmt = select(Plan).where(Plan.slug == "free")
        plan_result = await db.execute(plan_stmt)
        free_plan = plan_result.scalar_one_or_none()
        if not free_plan:
            raise HTTPException(status_code=500, detail="Default 'free' plan not found in database")

        # 3. Create the Tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name=payload.company_name,
            slug=payload.slug,
            gstin=payload.gstin,
            status="active",
            is_active=True
        )
        db.add(tenant)
        await db.flush() 

        # 4. Create the Subscription
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id=tenant_id,
            plan_id=free_plan.id,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30)
        )
        db.add(subscription)

        # 5. Generate and Hash Client Credentials
        client_id = f"lp_{secrets.token_hex(8)}"
        raw_secret = f"sk_{secrets.token_urlsafe(32)}"
        hashed_secret = hash_password(raw_secret)

        credential = ClientCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret_hash=hashed_secret,
            description="Initial onboarding key"
        )
        db.add(credential)

        await db.commit()

        # 6. Provision the Tenant Schema (Catalog/Orders)
        try:
            await ProvisioningService.provision_tenant_schema(tenant.slug)
        except Exception as e:
            print(f"CRITICAL: Tenant {tenant.slug} created but schema provisioning failed: {e}")

        # 7. Create the Tenant Admin User in Auth API with Retries
        auth_url = "http://launchpad-auth_api-1:8001/api/v1/internal/users"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        auth_url,
                        json={
                            "tenant_id": str(tenant_id),
                            "email": payload.admin_email,
                            "password": "Admin@2026",
                            "full_name": payload.admin_name
                        },
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        print(f"Successfully created admin user {payload.admin_email} on attempt {attempt + 1}")
                        break
                    else:
                        print(f"Auth API returned error: {response.text}")
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} failed to connect to Auth API: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    print("CRITICAL: Could not reach auth_api to create admin user after 3 attempts.")

        return TenantRegistrationResponse(
            tenant_id=str(tenant_id),
            slug=tenant.slug,
            client_id=client_id,
            client_secret=raw_secret,
            plan_name=free_plan.name
        )