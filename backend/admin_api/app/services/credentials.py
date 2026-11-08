import secrets
import uuid

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ResourceNotFoundError
from app.core.events import AdminEventType, raise_event
from app.models import ClientCredential, Tenant
from app.schemas.credentials import (
    CredentialCreate,
    CredentialCreated,
    CredentialRead,
    CredentialUpdate,
)
from app.services.common import transaction

password_hash = PasswordHash.recommended()


class CredentialService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ClientCredential]:
        if await self.session.get(Tenant, tenant_id) is None:
            raise ResourceNotFoundError("Tenant not found")
        query = (
            select(ClientCredential)
            .where(ClientCredential.tenant_id == tenant_id)
            .order_by(ClientCredential.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(query)).all())

    async def create(
        self,
        tenant_id: uuid.UUID,
        payload: CredentialCreate,
    ) -> CredentialCreated:
        async with transaction(self.session):
            tenant = await self.session.scalar(
                select(Tenant).where(Tenant.id == tenant_id).with_for_update()
            )
            if tenant is None:
                raise ResourceNotFoundError("Tenant not found")

            client_secret = secrets.token_urlsafe(48)
            credential = ClientCredential(
                tenant_id=tenant_id,
                client_id=f"lp_{secrets.token_urlsafe(24)}",
                client_secret_hash=password_hash.hash(client_secret),
                description=payload.description,
            )
            self.session.add(credential)
            await self.session.flush()
            await self.session.refresh(credential)

        result = CredentialCreated(
            **CredentialRead.model_validate(credential).model_dump(),
            client_secret=client_secret,
        )
        await raise_event(
            AdminEventType.CREDENTIAL_CREATED,
            "client_credential",
            credential.id,
            CredentialRead.model_validate(credential).model_dump(mode="json"),
        )
        return result

    async def update(
        self,
        credential_id: uuid.UUID,
        payload: CredentialUpdate,
    ) -> ClientCredential:
        async with transaction(self.session):
            credential = await self._get_for_update(credential_id)
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(credential, field, value)
            await self.session.flush()
            await self.session.refresh(credential)

        await raise_event(
            AdminEventType.CREDENTIAL_UPDATED,
            "client_credential",
            credential.id,
            CredentialRead.model_validate(credential).model_dump(mode="json"),
        )
        return credential

    async def revoke(self, credential_id: uuid.UUID) -> None:
        payload: dict | None = None
        async with transaction(self.session):
            credential = await self._get_for_update(credential_id)
            if credential.is_active:
                credential.is_active = False
                await self.session.flush()
                await self.session.refresh(credential)
                payload = CredentialRead.model_validate(credential).model_dump(mode="json")

        if payload is not None:
            await raise_event(
                AdminEventType.CREDENTIAL_REVOKED,
                "client_credential",
                credential_id,
                payload,
            )

    async def _get_for_update(self, credential_id: uuid.UUID) -> ClientCredential:
        credential = await self.session.scalar(
            select(ClientCredential)
            .where(ClientCredential.id == credential_id)
            .with_for_update()
        )
        if credential is None:
            raise ResourceNotFoundError("Client credential not found")
        return credential
