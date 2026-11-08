import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import (
    AuthNotFoundError,
    InvalidCredentialsError,
    RateLimitError,
    AuthValidationError,
)
from app.models import AuthToken, LoginAttempt, Session, User
from app.schemas.auth import (
    AuthTokens,
    PasswordChange,
    PasswordReset,
    UserRead,
    UserRegister,
    UserUpdateMe,
)
from app.services.common import transaction
from app.services.email import ensure_email_configured, send_action_email
from launchpad_shared.auth import create_access_token

password_hash = PasswordHash.recommended()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(
        self,
        payload: UserRegister,
        tenant_id: uuid.UUID | None,
    ) -> UserRead:
        if tenant_id is None:
            raise AuthValidationError("Tenant context is required for registration")
        ensure_email_configured()
        user = User(
            tenant_id=tenant_id,
            email=str(payload.email).strip().lower(),
            hashed_password=password_hash.hash(payload.password),
            full_name=payload.full_name,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        raw_token = secrets.token_urlsafe(48)
        async with transaction(self.session):
            self.session.add(user)
            await self.session.flush()
            self.session.add(
                AuthToken(
                    user_id=user.id,
                    token_hash=token_hash(raw_token),
                    email=user.email,
                    purpose="email_verification",
                    expires_at=utcnow()
                    + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
                )
            )
            await self.session.flush()
            await self.session.refresh(user)
        await send_action_email(user.email, raw_token, "email_verification")
        return UserRead.model_validate(user)

    async def login(
        self,
        *,
        email: str,
        password: str,
        tenant_id: uuid.UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthTokens:
        normalized_email = email.strip().lower()
        window_start = utcnow() - timedelta(minutes=settings.AUTH_LOGIN_WINDOW_MINUTES)
        user: User | None = None
        session_record: Session | None = None
        raw_refresh: str | None = None
        expires_at: datetime | None = None
        valid = False
        async with transaction(self.session):
            lock_key = f"auth-login:{tenant_id}:{normalized_email}:{ip_address}"
            await self.session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
                {"lock_key": lock_key},
            )
            attempts = await self.session.scalar(
                select(func.count(LoginAttempt.id)).where(
                    or_(
                        (LoginAttempt.email == normalized_email)
                        & (LoginAttempt.tenant_id == tenant_id),
                        LoginAttempt.ip_address == ip_address,
                    ),
                    LoginAttempt.created_at >= window_start,
                    LoginAttempt.succeeded.is_(False),
                )
            )
            if (attempts or 0) >= settings.AUTH_MAX_LOGIN_ATTEMPTS:
                raise RateLimitError("Too many login attempts; try again later")
            await self.session.execute(
                delete(LoginAttempt).where(
                    LoginAttempt.created_at < window_start - timedelta(days=1)
                )
            )
            await self.session.execute(
                delete(AuthToken).where(
                    (AuthToken.expires_at < utcnow() - timedelta(days=1))
                    | (
                        AuthToken.consumed_at.is_not(None)
                        & (AuthToken.consumed_at < utcnow() - timedelta(days=1))
                    )
                )
            )
            await self.session.execute(
                delete(Session).where(
                    Session.expires_at < utcnow() - timedelta(days=1)
                )
            )

            user = await self.session.scalar(
                select(User).where(
                    User.email == normalized_email,
                    User.tenant_id == tenant_id,
                )
            )
            valid = (
                user is not None
                and user.is_active
                and user.is_verified
                and password_hash.verify(password, user.hashed_password)
            )
            self.session.add(
                LoginAttempt(
                    email=normalized_email,
                    tenant_id=tenant_id,
                    ip_address=ip_address,
                    succeeded=bool(valid),
                )
            )
            if valid and user is not None:
                raw_refresh, session_record, expires_at = self._new_session(
                    user,
                    user_agent,
                    ip_address,
                )
                self.session.add(session_record)
                await self.session.flush()

        if not valid or user is None or session_record is None or expires_at is None or raw_refresh is None:
            raise InvalidCredentialsError()
        return self._tokens(user, session_record.id, raw_refresh)

    async def refresh(
        self,
        raw_refresh: str,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthTokens:
        replayed = False
        result: tuple[User, Session, str, datetime] | None = None
        async with transaction(self.session):
            current = await self.session.scalar(
                select(Session)
                .where(Session.refresh_token_hash == token_hash(raw_refresh))
                .with_for_update()
            )
            now = utcnow()
            if current is None:
                raise InvalidCredentialsError("Invalid refresh token")
            if current.revoked_at is not None:
                await self.session.execute(
                    update(Session)
                    .where(Session.family_id == current.family_id)
                    .values(revoked_at=now)
                )
                replayed = True
            elif current.expires_at <= now:
                current.revoked_at = now
            else:
                user = await self.session.get(User, current.user_id)
                if user is None or not user.is_active or not user.is_verified:
                    current.revoked_at = now
                else:
                    raw_new, next_session, expires_at = self._new_session(
                        user,
                        user_agent,
                        ip_address,
                        family_id=current.family_id,
                    )
                    self.session.add(next_session)
                    await self.session.flush()
                    current.revoked_at = now
                    current.replaced_by_session_id = next_session.id
                    result = (user, next_session, raw_new, expires_at)
        if replayed:
            raise InvalidCredentialsError("Refresh token reuse detected; sign in again")
        if result is None:
            raise InvalidCredentialsError("Invalid or expired refresh token")
        user, session_record, raw_token, expires_at = result
        return self._tokens(user, session_record.id, raw_token)

    async def logout(self, user_id: uuid.UUID, raw_refresh: str | None = None) -> None:
        async with transaction(self.session):
            query = select(Session).where(
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
            )
            if raw_refresh:
                query = query.where(Session.refresh_token_hash == token_hash(raw_refresh))
            records = (await self.session.scalars(query.with_for_update())).all()
            now = utcnow()
            for record in records:
                record.revoked_at = now

    async def verify_email(self, raw_token: str) -> UserRead:
        async with transaction(self.session):
            record = await self._consume_token(raw_token, "email_verification")
            user = await self.session.scalar(
                select(User).where(User.id == record.user_id).with_for_update()
            )
            if user is None:
                raise InvalidCredentialsError("Invalid or expired verification token")
            if record.email != user.email:
                raise InvalidCredentialsError("Invalid or expired verification token")
            user.is_verified = True
            await self.session.flush()
            await self.session.refresh(user)
        return UserRead.model_validate(user)

    async def resend_verification(self, email: str, tenant_id: uuid.UUID | None) -> None:
        ensure_email_configured()
        raw_token: str | None = None
        user: User | None = None
        async with transaction(self.session):
            user = await self.session.scalar(
                select(User).where(
                    User.email == email.strip().lower(),
                    User.tenant_id == tenant_id,
                )
            )
            if user is not None and not user.is_verified and user.is_active:
                raw_token = await self._store_action_token(user, "email_verification")
        if raw_token and user:
            await send_action_email(user.email, raw_token, "email_verification")

    async def request_password_reset(self, email: str, tenant_id: uuid.UUID | None) -> None:
        ensure_email_configured()
        raw_token: str | None = None
        user: User | None = None
        async with transaction(self.session):
            user = await self.session.scalar(
                select(User).where(
                    User.email == email.strip().lower(),
                    User.tenant_id == tenant_id,
                )
            )
            if user is not None and user.is_active:
                raw_token = await self._store_action_token(user, "password_reset")
        if raw_token and user:
            await send_action_email(user.email, raw_token, "password_reset")

    async def reset_password(self, payload: PasswordReset) -> None:
        async with transaction(self.session):
            record = await self._consume_token(payload.token, "password_reset")
            user = await self.session.scalar(
                select(User).where(User.id == record.user_id).with_for_update()
            )
            if user is None or not user.is_active:
                raise InvalidCredentialsError("Invalid or expired reset token")
            if record.email != user.email:
                raise InvalidCredentialsError("Invalid or expired reset token")
            user.hashed_password = password_hash.hash(payload.new_password)
            user.is_verified = True
            await self.session.execute(
                update(Session)
                .where(Session.user_id == user.id, Session.revoked_at.is_(None))
                .values(revoked_at=utcnow())
            )

    async def change_password(
        self,
        user_id: uuid.UUID,
        payload: PasswordChange,
    ) -> None:
        async with transaction(self.session):
            user = await self.session.scalar(
                select(User).where(User.id == user_id).with_for_update()
            )
            if user is None or not password_hash.verify(
                payload.current_password, user.hashed_password
            ):
                raise InvalidCredentialsError("Current password is incorrect")
            user.hashed_password = password_hash.hash(payload.new_password)
            await self.session.execute(
                update(Session)
                .where(
                    Session.user_id == user.id,
                    Session.revoked_at.is_(None),
                )
                .values(revoked_at=utcnow())
            )

    async def update_profile(
        self,
        user_id: uuid.UUID,
        payload: UserUpdateMe,
    ) -> UserRead:
        if "email" in payload.model_fields_set:
            ensure_email_configured()
        async with transaction(self.session):
            user = await self._get_user_for_update(user_id)
            changes = payload.model_dump(exclude_unset=True)
            if "email" in changes:
                new_email = str(changes.pop("email")).strip().lower()
                if new_email != user.email:
                    user.email = new_email
                    user.is_verified = False
                    raw_token = secrets.token_urlsafe(48)
                    self.session.add(
                        AuthToken(
                            user_id=user.id,
                            token_hash=token_hash(raw_token),
                            email=user.email,
                            purpose="email_verification",
                            expires_at=utcnow()
                            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
                        )
                    )
                else:
                    raw_token = None
            else:
                raw_token = None
            for field, value in changes.items():
                setattr(user, field, value)
            await self.session.flush()
            await self.session.refresh(user)
        if raw_token:
            await send_action_email(user.email, raw_token, "email_verification")
        return UserRead.model_validate(user)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise AuthNotFoundError("User not found")
        return user

    def _new_session(
        self,
        user: User,
        user_agent: str | None,
        ip_address: str | None,
        *,
        family_id: uuid.UUID | None = None,
    ) -> tuple[str, Session, datetime]:
        raw_refresh = secrets.token_urlsafe(48)
        expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session_record = Session(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            refresh_token_hash=token_hash(raw_refresh),
            user_agent=user_agent[:255] if user_agent else None,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        return raw_refresh, session_record, expires_at

    def _tokens(
        self,
        user: User,
        session_id: uuid.UUID,
        raw_refresh: str,
    ) -> AuthTokens:
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=user.tenant_id,
            is_superuser=user.is_superuser,
            secret_key=settings.SECRET_KEY,
            expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            extra_claims={"sid": str(session_id)},
        )
        return AuthTokens(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def _store_action_token(self, user: User, purpose: str) -> str:
        raw_token = secrets.token_urlsafe(48)
        now = utcnow()
        expires_at = (
            now + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
            if purpose == "email_verification"
            else now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )
        await self.session.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user.id,
                AuthToken.purpose == purpose,
                AuthToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        self.session.add(
            AuthToken(
                user_id=user.id,
                token_hash=token_hash(raw_token),
                email=user.email,
                purpose=purpose,
                expires_at=expires_at,
            )
        )
        return raw_token

    async def _consume_token(self, raw_token: str, purpose: str) -> AuthToken:
        record = await self.session.scalar(
            select(AuthToken)
            .where(
                AuthToken.token_hash == token_hash(raw_token),
                AuthToken.purpose == purpose,
                AuthToken.consumed_at.is_(None),
            )
            .with_for_update()
        )
        if record is None or record.expires_at <= utcnow():
            raise InvalidCredentialsError("Invalid or expired token")
        record.consumed_at = utcnow()
        return record

    async def _get_user_for_update(self, user_id: uuid.UUID) -> User:
        user = await self.session.scalar(
            select(User).where(User.id == user_id).with_for_update()
        )
        if user is None:
            raise AuthNotFoundError("User not found")
        return user
