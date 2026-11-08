from pydantic import EmailStr
from launchpad_shared.schemas import BaseSchema

class UserRegister(BaseSchema):
    email: EmailStr
    password: str
    full_name: str | None = None
    tenant_id: str | None = None  # If empty, creates a superuser

class UserLogin(BaseSchema):
    email: EmailStr
    password: str

class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseSchema):
    id: str
    email: str
    full_name: str | None
    is_superuser: bool
    is_active: bool