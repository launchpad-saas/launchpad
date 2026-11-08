import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Session, User
from launchpad_shared.auth import AuthClaims, require_auth


async def get_current_user(
    claims: AuthClaims = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> User:
    if claims.session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing its session identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = uuid.UUID(claims.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_session = await session.get(Session, claims.session_id)
    user = await session.get(User, user_id)
    if (
        auth_session is None
        or auth_session.user_id != user_id
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= datetime.now(timezone.utc)
        or user is None
        or not user.is_active
        or not user.is_verified
        or claims.tenant_id != user.tenant_id
        or claims.is_superuser != user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
