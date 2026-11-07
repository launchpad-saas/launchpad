from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from launchpad_shared.middleware import TenantMiddleware
from launchpad_shared.schemas import BaseSchema
from launchpad_shared import configure_tenant_engine
from app.core.config import settings
from app.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tenant_engine(settings.DATABASE_URL)
    yield


class RootResponse(BaseSchema):
    service: str
    status: str


app = FastAPI(title="orders_api", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TenantMiddleware)
app.include_router(health_router, prefix="/api/v1")


@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(service="orders_api", status="ok")