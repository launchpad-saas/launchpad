from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthConflictError


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[None]:
    try:
        if session.in_transaction():
            await session.commit()
        async with session.begin():
            yield
    except IntegrityError as exc:
        raise AuthConflictError("The operation conflicts with existing data") from exc
