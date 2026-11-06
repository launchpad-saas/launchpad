"""Subscription — binds a Tenant to a Plan for a billing period."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
    )

    # Status: trialing | active | past_due | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trialing")
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Payment provider references (Stripe, Paddle, etc.)
    external_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")  # noqa: F821
    plan: Mapped["Plan"] = relationship("Plan")  # noqa: F821