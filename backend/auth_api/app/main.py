from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from launchpad_shared.middleware import TenantMiddleware
from launchpad_shared.schemas import BaseSchema
from launchpad_shared import configure_tenant_engine
from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tenant_engine(settings.DATABASE_URL)
    yield

class RootResponse(BaseSchema):
    service: str
    status: str

app = FastAPI(title="auth_api", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TenantMiddleware)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")

@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(service="auth_api", status="ok")