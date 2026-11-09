"""FastAPI auth dependencies."""

import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from launchpad_shared.auth import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_jwt_secret_key() -> str:
    """Helper to get the secret key for JWT signing/decoding."""
    return os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")


@dataclass(frozen=True)
class AuthClaims:
    sub: str
    tenant_id: UUID | None
    roles: list[str]
    is_superuser: bool = False


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthClaims:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(
            credentials.credentials, 
            secret_key=get_jwt_secret_key()
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_raw = payload.get("tenant_id")
    return AuthClaims(
        sub=payload.get("sub", ""),
        tenant_id=UUID(tenant_raw) if tenant_raw else None,
        roles=payload.get("roles") or [],
        is_superuser=payload.get("is_superuser", False),
    )


async def require_superuser(claims: AuthClaims = Depends(require_auth)) -> AuthClaims:
    if not claims.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required",
        )
    return claims