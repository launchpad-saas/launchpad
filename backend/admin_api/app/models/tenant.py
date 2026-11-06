"""Tenant — a SaaS customer (company/account).

Each tenant gets its own isolated e-commerce databases
(tenant_<slug>_catalog and tenant_<slug>_orders).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Per-tenant database names (both null until provisioning completes)
    catalog_db_name: Mapped[str | None] = mapped_column(String(63), nullable=True)
    orders_db_name: Mapped[str | None] = mapped_column(String(63), nullable=True)

    # Status: pending | active | suspended | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    credentials: Mapped[list["ClientCredential"]] = relationship(  # noqa: F821
        "ClientCredential", back_populates="tenant", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="tenant", cascade="all, delete-orphan"
    )