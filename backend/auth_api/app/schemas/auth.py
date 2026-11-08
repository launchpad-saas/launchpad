import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class AuthSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=None,
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )


class UserRead(AuthSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserRegister(AuthSchema):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserRegister):
    tenant_id: uuid.UUID | None = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = True

    @model_validator(mode="after")
    def validate_tenant_scope(self):
        if self.is_superuser and self.tenant_id is not None:
            raise ValueError("Superusers must not be assigned to a tenant")
        if not self.is_superuser and self.tenant_id is None:
            raise ValueError("Tenant users must be assigned to a tenant")
        return self


class UserUpdate(AuthSchema):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

    @model_validator(mode="after")
    def reject_null_non_nullable(self):
        for field in ("email", "is_active", "is_superuser", "is_verified"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class UserUpdateMe(AuthSchema):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def reject_null_email(self):
        if "email" in self.model_fields_set and self.email is None:
            raise ValueError("email cannot be null")
        return self


class PasswordChange(AuthSchema):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class PasswordReset(AuthSchema):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)


class TokenRefresh(AuthSchema):
    refresh_token: str = Field(min_length=32, max_length=256)


class TokenAction(AuthSchema):
    token: str = Field(min_length=32, max_length=256)


class AuthTokens(AuthSchema):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserList(AuthSchema):
    data: list[UserRead]
    count: int


class Message(AuthSchema):
    message: str
