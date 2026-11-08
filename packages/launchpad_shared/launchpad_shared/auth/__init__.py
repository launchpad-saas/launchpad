"""JWT + password utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt
from pwdlib import PasswordHash

DEFAULT_SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hash.verify(plain, hashed)


def create_access_token(
    *,
    subject: str,
    tenant_id: UUID | None,
    roles: list[str] | None = None,
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
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret_key: str = DEFAULT_SECRET_KEY,
    algorithm: str = DEFAULT_ALGORITHM,
) -> dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])


# Export dependencies
from .dependencies import AuthClaims, require_auth, require_superuser  # noqa: E402,F401