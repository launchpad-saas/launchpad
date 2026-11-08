from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from launchpad_shared.middleware import TenantMiddleware
from launchpad_shared.schemas import BaseSchema
from app.api.health import router as health_router
from app.api.tenants import router as tenant_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

class RootResponse(BaseSchema):
    service: str
    status: str

app = FastAPI(title="admin_api", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TenantMiddleware)
app.include_router(health_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1/tenants")

@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(service="admin_api", status="ok")