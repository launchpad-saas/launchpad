"""Tenant-scoped async DB session.

Opens a connection to the shared tenant database and switches the
search_path to the tenant's schema before yielding the session.

Usage in FastAPI:

    from launchpad_shared.db.session import get_tenant_session

    async def some_route(request: Request):
        tenant_slug = request.state.tenant_slug  # set by TenantMiddleware
        async with get_tenant_session(tenant_slug) as session:
            result = await session.execute(select(Product))
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import quoted_name

from launchpad_shared.db.slug import validate_tenant_slug

# Engine and sessionmaker are created lazily on first use.
# This avoids requiring DATABASE_URL at import time (helps with unit tests).
_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _get_engine(database_url: str | None = None):
    global _engine, _sessionmaker
    if _engine is None:
        if database_url is None:
            raise RuntimeError(
                "get_tenant_session requires a DATABASE_URL on first call. "
                "Pass it explicitly or set up the engine via configure_tenant_engine()."
            )
        _engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
        _sessionmaker = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine, _sessionmaker


def configure_tenant_engine(database_url: str) -> None:
    """Explicitly configure the shared tenant engine.

    Call this once at app startup (in main.py) to point at launchpad_tenant.
    """
    global _engine, _sessionmaker
    if _engine is not None:
        # Already configured — no-op
        return
    _engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )


@asynccontextmanager
async def get_tenant_session(
    tenant_slug: str,
    *,
    database_url: str | None = None,
) -> AsyncIterator[AsyncSession]:
    """Yield an async session scoped to the tenant's schema.

    The `search_path` is set to `"<slug>", public` for this session only.
    Unqualified table references (e.g. `products`) will hit the tenant's
    schema; `public` is the fallback for any shared lookups.

    Raises:
        InvalidTenantSlug: if slug is invalid or reserved.
    """
    # 1. Validate first — defense in depth
    validate_tenant_slug(tenant_slug)

    # 2. Get the engine
    engine, sessionmaker = _get_engine(database_url)

    # 3. Open a session
    async with sessionmaker() as session:
        try:
            # 4. Switch schema for THIS session only.
            #    quoted_name(..., quote=True) wraps in double quotes → safe.
            schema_id = quoted_name(tenant_slug, quote=True)
            await session.execute(text(f"SET search_path TO {schema_id}, public"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # 5. Reset search_path so the connection (if reused from pool)
            #    doesn't leak tenant context to the next request.
            try:
                await session.execute(text("SET search_path TO public"))
            except Exception:
                pass