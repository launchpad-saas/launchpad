from pydantic import EmailStr, Field
from launchpad_shared.schemas import BaseSchema

class TenantCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=3, max_length=63, pattern=r"^[a-z][a-z0-9_]{2,62}$")
    legal_business_name: str | None = Field(None, max_length=255)
    gstin: str | None = Field(None, min_length=15, max_length=15)
    support_email: EmailStr | None = None

class TenantResponse(BaseSchema):
    id: str
    name: str
    slug: str
    status: str
    is_active: bool