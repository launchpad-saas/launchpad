import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from launchpad_shared.db import validate_tenant_slug
from launchpad_shared.schemas import BaseSchema

TenantStatus = Literal["pending", "active", "suspended", "cancelled"]


class TenantCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=63)
    is_active: bool = True
    status: TenantStatus = "pending"
    catalog_db_name: str | None = Field(default=None, max_length=63)
    orders_db_name: str | None = Field(default=None, max_length=63)
    legal_business_name: str | None = Field(default=None, max_length=255)
    gstin: str | None = Field(default=None, max_length=15)
    cin: str | None = Field(default=None, max_length=21)
    pan: str | None = Field(default=None, max_length=10)
    support_email: str | None = Field(default=None, max_length=255)
    support_phone: str | None = Field(default=None, max_length=20)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    country: str = Field(default="IN", min_length=2, max_length=2)
    logo_url: str | None = Field(default=None, max_length=500)
    favicon_url: str | None = Field(default=None, max_length=500)
    branding_settings: dict = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str):
        return validate_tenant_slug(value)


class TenantUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    status: TenantStatus | None = None
    catalog_db_name: str | None = Field(default=None, max_length=63)
    orders_db_name: str | None = Field(default=None, max_length=63)
    legal_business_name: str | None = Field(default=None, max_length=255)
    gstin: str | None = Field(default=None, max_length=15)
    cin: str | None = Field(default=None, max_length=21)
    pan: str | None = Field(default=None, max_length=10)
    support_email: str | None = Field(default=None, max_length=255)
    support_phone: str | None = Field(default=None, max_length=20)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    logo_url: str | None = Field(default=None, max_length=500)
    favicon_url: str | None = Field(default=None, max_length=500)
    branding_settings: dict | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("name", "is_active", "status", "country", "branding_settings"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class TenantRead(TenantCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
