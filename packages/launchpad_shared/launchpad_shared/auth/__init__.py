"""JWT + password utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt
from passlib.context import CryptContext

DEFAULT_SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    *,
    subject: str,
    tenant_id: UUID | None,
    roles: list[str] | None = None,
    is_superuser: bool = False,
    secret_key: str = DEFAULT_SECRET_KEY,
    algorithm: str = DEFAULT_ALGORITHM,
    expires_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "roles": roles or [],
        "is_superuser": is_superuser,
    }
    if extra_claims:
        reserved_claims = payload.keys() & extra_claims.keys()
        if reserved_claims:
            raise ValueError(
                f"extra_claims cannot override registered claims: {sorted(reserved_claims)}"
            )
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret_key: str = DEFAULT_SECRET_KEY,
    algorithm: str = DEFAULT_ALGORITHM,
) -> dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])


# Re-export dependency layer so services can share the same JWT policy.
from .dependencies import (  # noqa: E402,F401
    AuthClaims,
    get_jwt_secret_key,
    require_auth,
    require_superuser,
)