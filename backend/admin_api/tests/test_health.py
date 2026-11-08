import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.core.config import settings
from app.core.events import AdminEventType, raise_event, register_event_handler
from app.main import app
from app.schemas.tenants import TenantCreate
from app.services.credentials import CredentialService
from app.services.plans import PlanService
from app.services.subscriptions import SubscriptionService
from app.services.tenants import TenantService
from launchpad_shared.auth import create_access_token, require_auth, require_superuser

client = TestClient(app)


class FakeTransaction:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        self.session.committed = False

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.session.committed = exc_type is None


class FakeSession:
    def __init__(self):
        self.committed = False

    def begin(self):
        return FakeTransaction(self)

    def add(self, instance):
        self.instance = instance

    async def flush(self):
        self.instance.id = uuid.uuid4()
        self.instance.created_at = datetime.now(timezone.utc)
        self.instance.updated_at = datetime.now(timezone.utc)

    async def refresh(self, instance):
        pass


class LockSession:
    async def scalar(self, statement):
        self.statement = statement
        return object()


class FailedFlushSession(FakeSession):
    async def flush(self):
        raise RuntimeError("database failure")


def test_health_no_tenant():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "admin_api"


def test_health_with_tenant():
    r = client.get("/api/v1/health", headers={"X-Tenant-ID": "11111111-1111-1111-1111-111111111111"})
    assert r.status_code == 200
    assert r.json()["tenantId"] is None


def test_admin_api_ignores_invalid_tenant_header():
    response = client.get("/api/v1/health", headers={"X-Tenant-ID": "not-a-uuid"})

    assert response.status_code == 200
    assert response.json()["tenantId"] is None


def test_management_api_requires_bearer_token():
    response = client.get("/api/v1/tenants")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_management_api_rejects_non_superuser_token():
    token = create_access_token(
        subject="user@example.com",
        tenant_id=None,
        secret_key=settings.SECRET_KEY,
    )

    response = client.get(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_management_api_accepts_superuser_claim():
    token = create_access_token(
        subject="owner@example.com",
        tenant_id=None,
        secret_key=settings.SECRET_KEY,
        is_superuser=True,
    )

    claims = asyncio.run(
        require_auth(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            secret_key=settings.SECRET_KEY,
        )
    )

    assert claims.is_superuser is True
    assert claims.tenant_id is None
    assert asyncio.run(require_superuser(claims)) is claims


def test_management_api_routes_are_registered_and_protected():
    paths = app.openapi()["paths"]
    expected_methods = {
        "/api/v1/tenants": {"get", "post"},
        "/api/v1/tenants/{tenant_id}": {"get", "patch", "delete"},
        "/api/v1/tenants/{tenant_id}/credentials": {"get", "post"},
        "/api/v1/credentials/{credential_id}": {"patch", "delete"},
        "/api/v1/plans": {"get", "post"},
        "/api/v1/plans/{plan_id}": {"get", "patch", "delete"},
        "/api/v1/subscriptions": {"get", "post"},
        "/api/v1/subscriptions/{subscription_id}": {"get", "patch", "delete"},
    }

    for path, methods in expected_methods.items():
        for method in methods:
            assert paths[path][method]["security"] == [{"HTTPBearer": []}]


def test_tenant_slug_must_be_valid_for_tenant_schemas():
    TenantCreate(name="Example", slug="example_shop")

    with pytest.raises(ValidationError):
        TenantCreate(name="Example", slug="admin_api")


def test_admin_events_are_dispatched():
    received = []

    async def handler(event):
        received.append(event)

    unregister = register_event_handler(handler)
    try:
        asyncio.run(
            raise_event(
                AdminEventType.TENANT_CREATED,
                "tenant",
                uuid.UUID("11111111-1111-1111-1111-111111111111"),
                {"slug": "example_shop"},
            )
        )
    finally:
        unregister()

    assert len(received) == 1
    assert received[0].event_type is AdminEventType.TENANT_CREATED
    assert received[0].payload == {"slug": "example_shop"}


def test_service_emits_event_after_transaction_commit():
    session = FakeSession()
    received = []

    async def handler(event):
        received.append((session.committed, event))

    unregister = register_event_handler(handler)
    try:
        asyncio.run(
            TenantService(session).create(
                TenantCreate(name="Example", slug="example_shop")
            )
        )
    finally:
        unregister()

    assert received[0][0] is True
    assert received[0][1].event_type is AdminEventType.TENANT_CREATED


def test_service_does_not_emit_event_when_transaction_fails():
    received = []

    async def handler(event):
        received.append(event)

    unregister = register_event_handler(handler)
    try:
        with pytest.raises(RuntimeError, match="database failure"):
            asyncio.run(
                TenantService(FailedFlushSession()).create(
                    TenantCreate(name="Example", slug="example_shop")
                )
            )
    finally:
        unregister()

    assert received == []


def test_mutation_services_select_rows_for_update():
    async def verify_locks():
        for service_type in (
            TenantService,
            PlanService,
            CredentialService,
            SubscriptionService,
        ):
            session = LockSession()
            service = service_type(session)
            await service._get_for_update(uuid.uuid4())
            statement = str(session.statement.compile(dialect=postgresql.dialect()))
            assert "FOR UPDATE" in statement

    asyncio.run(verify_locks())