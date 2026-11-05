"""Tenant isolation middleware."""

import uuid
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        raw = request.headers.get("X-Tenant-ID")
        if raw is None:
            request.state.tenant_id = None
            return await call_next(request)

        try:
            request.state.tenant_id = uuid.UUID(raw)
        except (ValueError, AttributeError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_tenant_id",
                    "message": "X-Tenant-ID must be a valid UUID.",
                },
            )

        return await call_next(request)
