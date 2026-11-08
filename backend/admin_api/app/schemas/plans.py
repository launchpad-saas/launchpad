import uuid
from datetime import datetime

from pydantic import Field, model_validator

from launchpad_shared.schemas import BaseSchema


class PlanCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    price_cents: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_active: bool = True
    features: dict = Field(default_factory=dict)


class PlanUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    features: dict | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("name", "slug", "price_cents", "currency", "is_active", "features"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class PlanRead(PlanCreate):
    id: uuid.UUID
    created_at: datetime
