import uuid
from datetime import datetime

from pydantic import Field, model_validator

from launchpad_shared.schemas import BaseSchema


class CredentialCreate(BaseSchema):
    description: str | None = Field(default=None, max_length=255)


class CredentialUpdate(BaseSchema):
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_active(self):
        if "is_active" in self.model_fields_set and self.is_active is None:
            raise ValueError("is_active cannot be null")
        return self


class CredentialRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    client_id: str
    description: str | None
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime


class CredentialCreated(CredentialRead):
    client_secret: str
