from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from launchpad_shared.middleware import TenantMiddleware
from launchpad_shared.schemas import BaseSchema
from app.core.config import settings
from app.core.errors import AuthAPIError
from launchpad_shared.auth import get_jwt_secret_key
from app.api.health import router as health_router
from app.api.internal import router as internal_router


class RootResponse(BaseSchema):
    service: str
    status: str


app = FastAPI(title="auth_api", version="0.1.0")
app.dependency_overrides[get_jwt_secret_key] = lambda: settings.SECRET_KEY


@app.exception_handler(AuthAPIError)
async def auth_api_error_handler(_request: Request, exc: AuthAPIError) -> JSONResponse:
    headers = {}
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    if exc.status_code == 429:
        headers["Retry-After"] = str(settings.AUTH_LOGIN_WINDOW_MINUTES * 60)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TenantMiddleware)
app.include_router(health_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1/internal")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(service="auth_api", status="ok")