from pydantic import Field
from launchpad_shared.schemas import BaseSchema

class PlanCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=50)
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9_-]+$")
    price_cents: int = Field(..., ge=0)
    currency: str = Field(default="INR", max_length=3)
    features: dict = Field(default_factory=dict)

class PlanResponse(BaseSchema):
    id: str
    name: str
    slug: str
    price_cents: int
    currency: str
    is_active: bool