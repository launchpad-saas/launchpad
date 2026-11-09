from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

from app.core.config import settings
from app.db.base import Base
from app.models import Category, Product

router = APIRouter(tags=["internal"])

class ProvisionRequest(BaseModel):
    slug: str

@router.post("/provision")
async def provision_schema(payload: ProvisionRequest):
    schema_name = payload.slug
    if not schema_name.isidentifier():
        raise HTTPException(status_code=400, detail="Invalid schema name")

    # 1. Create the schema
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
            await conn.commit()
    finally:
        await engine.dispose()

    # 2. Create tables in the schema
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            # Set the search_path so SQLAlchemy creates tables in the new schema
            await conn.execute(text(f'SET search_path TO "{schema_name}", public'))
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
    except Exception as e:
        print(f"Table creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tables")
    finally:
        await engine.dispose()

    return {"status": "ok", "schema": schema_name, "tables_created": True}

@router.get("/health")
async def internal_health():
    return {"status": "ok"}