from pydantic import EmailStr, Field
from launchpad_shared.schemas import BaseSchema

class TenantRegistrationRequest(BaseSchema):
    company_name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=3, max_length=63, pattern=r"^[a-z][a-z0-9_]{2,62}$")
    admin_email: EmailStr
    admin_name: str = Field(..., min_length=2, max_length=255)
    gstin: str | None = Field(None, min_length=15, max_length=15)

class TenantRegistrationResponse(BaseSchema):
    tenant_id: str
    slug: str
    client_id: str
    client_secret: str  # ONLY returned once!
    plan_name: str