import uuid
from datetime import datetime, timezone

from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthNotFoundError
from app.models import Session, User
from app.schemas.auth import UserCreate, UserRead, UserUpdate
from app.services.common import transaction

password_hash = PasswordHash.recommended()


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, *, offset: int = 0, limit: int = 100) -> tuple[list[User], int]:
        total = await self.session.scalar(select(func.count(User.id)))
        users = await self.session.scalars(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(users.all()), total or 0

    async def create(self, payload: UserCreate) -> User:
        async with transaction(self.session):
            user = User(
                tenant_id=payload.tenant_id,
                email=str(payload.email).strip().lower(),
                hashed_password=password_hash.hash(payload.password),
                full_name=payload.full_name,
                is_active=payload.is_active,
                is_superuser=payload.is_superuser,
                is_verified=payload.is_verified,
            )
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def update(self, user_id: uuid.UUID, payload: UserUpdate) -> User:
        async with transaction(self.session):
            user = await self._get_for_update(user_id)
            changes = payload.model_dump(exclude_unset=True)
            password = changes.pop("password", None)
            email = changes.get("email")
            if email is not None:
                changes["email"] = str(email).strip().lower()
                if changes["email"] != user.email:
                    changes["is_verified"] = False
            for field, value in changes.items():
                setattr(user, field, value)
            if password is not None:
                user.hashed_password = password_hash.hash(password)
                sessions = await self.session.scalars(
                    select(Session)
                    .where(Session.user_id == user_id, Session.revoked_at.is_(None))
                    .with_for_update()
                )
                now = datetime.now(timezone.utc)
                for session_record in sessions:
                    session_record.revoked_at = now
            elif changes.get("is_active") is False or "is_superuser" in changes:
                sessions = await self.session.scalars(
                    select(Session)
                    .where(Session.user_id == user_id, Session.revoked_at.is_(None))
                    .with_for_update()
                )
                now = datetime.now(timezone.utc)
                for session_record in sessions:
                    session_record.revoked_at = now
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def delete(self, user_id: uuid.UUID) -> None:
        async with transaction(self.session):
            user = await self._get_for_update(user_id)
            await self.session.delete(user)

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise AuthNotFoundError("User not found")
        return user

    async def _get_for_update(self, user_id: uuid.UUID) -> User:
        user = await self.session.scalar(
            select(User).where(User.id == user_id).with_for_update()
        )
        if user is None:
            raise AuthNotFoundError("User not found")
        return user
