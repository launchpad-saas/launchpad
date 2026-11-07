"""Tenant-scoped DB session for catalog_api."""

from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from launchpad_shared import configure_tenant_engine, get_tenant_session
from app.core.config import settings

# Configure the shared engine once at import time.
configure_tenant_engine(settings.DATABASE_URL)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a tenant-scoped DB session.

    Tenant slug is resolved by:
    1. `X-Tenant-ID` header (set by ClientAuthMiddleware in Phase 3.5)
    2. Falls back to `DEFAULT_TENANT_SCHEMA` (dev/testing before onboarding)
    """
    tenant_slug = getattr(request.state, "tenant_slug", None) or settings.DEFAULT_TENANT_SCHEMA
    async with get_tenant_session(tenant_slug) as session:
        yield session