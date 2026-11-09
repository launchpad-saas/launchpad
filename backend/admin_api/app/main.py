from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.credentials import router as credentials_router
from app.api.health import router as health_router
from app.api.onboarding import router as onboarding_router
from app.api.plans import router as plans_router
from app.api.subscriptions import router as subscriptions_router
from app.api.tenants import router as tenants_router
from app.core.config import settings
from app.core.errors import AdminAPIError
from launchpad_shared.auth import get_jwt_secret_key
from launchpad_shared.schemas import BaseSchema


class RootResponse(BaseSchema):
    service: str
    status: str


app = FastAPI(title="admin_api", version="0.1.0")
app.dependency_overrides[get_jwt_secret_key] = lambda: settings.SECRET_KEY


@app.exception_handler(AdminAPIError)
async def admin_api_error_handler(_request: Request, exc: AdminAPIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1/onboarding")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(credentials_router, prefix="/api/v1")
app.include_router(plans_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")


@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(service="admin_api", status="ok")