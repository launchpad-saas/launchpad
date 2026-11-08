"""Tenant — a SaaS customer (company/account).

Stores identity, branding, and legal/compliance details.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
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

    # --- Tenant Database Schemas ---
    catalog_db_name: Mapped[str | None] = mapped_column(String(63), nullable=True)
    orders_db_name: Mapped[str | None] = mapped_column(String(63), nullable=True)

    # Status: pending | active | suspended | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # --- Legal & Business Details (India Focus) ---
    legal_business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)  # 15-char GSTIN
    cin: Mapped[str | None] = mapped_column(String(21), nullable=True)   # 21-char LLP CIN
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)   # 10-char PAN
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Physical Address
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="IN")

    # --- Storefront Branding (Customization) ---
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Branding settings: {"primary_color": "#ff0000", "font": "Inter", "hero_text": "..."}
    branding_settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

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