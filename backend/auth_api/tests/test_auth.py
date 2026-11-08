import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.auth import UserCreate
from launchpad_shared.auth import create_access_token, decode_access_token

client = TestClient(app)


def test_auth_endpoints_are_registered():
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/login/access-token",
        "/api/v1/login/refresh",
        "/api/v1/login/logout",
        "/api/v1/login/logout-all",
        "/api/v1/users/signup",
        "/api/v1/users/me",
        "/api/v1/users/me/password",
        "/api/v1/users/",
        "/api/v1/users/{user_id}",
        "/api/v1/password-recovery/{email}",
        "/api/v1/reset-password/",
        "/api/v1/verify-email",
    }

    assert expected <= paths.keys()


def test_current_user_route_requires_bearer_token():
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_tenant_user_cannot_be_created_without_tenant():
    with pytest.raises(ValidationError):
        UserCreate(email="customer@example.com", password="long-password-123")


def test_superuser_must_not_be_assigned_to_tenant():
    with pytest.raises(ValidationError):
        UserCreate(
            email="owner@example.com",
            password="long-password-123",
            is_superuser=True,
            tenant_id=uuid.uuid4(),
        )


def test_superuser_access_token_has_expected_platform_claims():
    token = create_access_token(
        subject="owner-id",
        tenant_id=None,
        is_superuser=True,
        extra_claims={"sid": str(uuid.uuid4())},
    )
    claims = decode_access_token(token)

    assert claims["is_superuser"] is True
    assert claims["tenant_id"] is None


def test_extra_claims_cannot_override_authentication_claims():
    with pytest.raises(ValueError, match="cannot override registered claims"):
        create_access_token(
            subject="customer-id",
            tenant_id=None,
            extra_claims={"is_superuser": True},
        )


def test_login_rate_limit_is_configurable():
    from app.core.config import settings

    assert settings.AUTH_MAX_LOGIN_ATTEMPTS > 0
    assert settings.AUTH_LOGIN_WINDOW_MINUTES > 0
