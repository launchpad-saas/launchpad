import asyncio
import getpass

from pwdlib import PasswordHash
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import User


async def main() -> None:
    email = input("Superuser email: ").strip().lower()
    email = str(TypeAdapter(EmailStr).validate_python(email))
    password = getpass.getpass("Password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    async with SessionLocal() as session:
        async with session.begin():
            existing = await session.scalar(
                select(User).where(User.email == email, User.tenant_id.is_(None))
            )
            if existing is not None:
                raise SystemExit("A platform user with that email already exists")
            session.add(
                User(
                    tenant_id=None,
                    email=email,
                    hashed_password=PasswordHash.recommended().hash(password),
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                )
            )
    await engine.dispose()
    print(f"Created platform superuser: {email}")


if __name__ == "__main__":
    asyncio.run(main())
