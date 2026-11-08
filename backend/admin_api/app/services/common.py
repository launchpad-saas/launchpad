from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ResourceConflictError


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[None]:
    try:
        async with session.begin():
            yield
    except IntegrityError as exc:
        raise ResourceConflictError() from exc
