import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class AdminEventType(StrEnum):
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"
    PLAN_DELETED = "plan.deleted"
    CREDENTIAL_CREATED = "credential.created"
    CREDENTIAL_UPDATED = "credential.updated"
    CREDENTIAL_REVOKED = "credential.revoked"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_DELETED = "subscription.deleted"


@dataclass(frozen=True)
class AdminEvent:
    event_type: AdminEventType
    resource: str
    resource_id: UUID
    occurred_at: datetime
    payload: dict[str, Any]


EventHandler = Callable[[AdminEvent], Awaitable[None]]
_handlers: list[EventHandler] = []


def register_event_handler(handler: EventHandler) -> Callable[[], None]:
    _handlers.append(handler)

    def unregister() -> None:
        _handlers.remove(handler)

    return unregister


async def raise_event(
    event_type: AdminEventType,
    resource: str,
    resource_id: UUID,
    payload: dict[str, Any],
) -> None:
    event = AdminEvent(
        event_type=event_type,
        resource=resource,
        resource_id=resource_id,
        occurred_at=datetime.now(timezone.utc),
        payload=payload,
    )
    for handler in tuple(_handlers):
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Admin event handler failed after commit",
                extra={
                    "event_type": event.event_type,
                    "resource": event.resource,
                    "resource_id": str(event.resource_id),
                },
            )
