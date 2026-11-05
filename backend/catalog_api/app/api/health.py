from fastapi import APIRouter, Request
from launchpad_shared.schemas import BaseSchema

router = APIRouter(tags=["health"])


class HealthResponse(BaseSchema):
    status: str
    service: str
    tenant_id: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    tid = getattr(request.state, "tenant_id", None)
    return HealthResponse(status="ok", service="catalog_api", tenant_id=str(tid) if tid else None)