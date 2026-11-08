import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from launchpad_shared.schemas import BaseSchema

SubscriptionStatus = Literal["trialing", "active", "past_due", "cancelled"]


class SubscriptionCreate(BaseSchema):
    tenant_id: uuid.UUID
    plan_id: uuid.UUID
    status: SubscriptionStatus = "trialing"
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    external_customer_id: str | None = Field(default=None, max_length=255)
    external_subscription_id: str | None = Field(default=None, max_length=255)

    @field_validator("current_period_start", "current_period_end")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("billing period timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_period(self):
        if self.current_period_end <= self.current_period_start:
            raise ValueError("current_period_end must be after current_period_start")
        return self


class SubscriptionUpdate(BaseSchema):
    plan_id: uuid.UUID | None = None
    status: SubscriptionStatus | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool | None = None
    external_customer_id: str | None = Field(default=None, max_length=255)
    external_subscription_id: str | None = Field(default=None, max_length=255)

    @field_validator("current_period_start", "current_period_end")
    @classmethod
    def require_timezone(cls, value: datetime | None):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("billing period timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        for field in (
            "plan_id",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class SubscriptionRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    plan_id: uuid.UUID
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    external_customer_id: str | None
    external_subscription_id: str | None
    created_at: datetime
    updated_at: datetime
