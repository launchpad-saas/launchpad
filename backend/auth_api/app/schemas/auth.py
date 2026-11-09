from pydantic import EmailStr
from launchpad_shared.schemas import BaseSchema

class UserRegister(BaseSchema):
    email: EmailStr
    password: str
    full_name: str | None = None
    tenant_id: str | None = None

class UserLogin(BaseSchema):
    email: EmailStr
    password: str

class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseSchema):
    refresh_token: str

class UserResponse(BaseSchema):
    id: str
    email: str
    full_name: str | None
    is_superuser: bool
    is_active: bool

# --- Added to fix the AuthTokens ImportError ---
class AuthTokens(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"