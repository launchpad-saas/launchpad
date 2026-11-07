"""Tenant slug validation.

A tenant slug is used directly as a PostgreSQL schema name.
Every slug MUST pass through `validate_tenant_slug()` before use.

Rules:
- Must match ^[a-z][a-z0-9_]{2,40}$
- Cannot be a reserved schema name
- Cannot be a PostgreSQL system schema
"""

import re

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,40}$")

RESERVED_SCHEMAS: set[str] = {
    # PostgreSQL system schemas
    "public",
    "pg_catalog",
    "pg_toast",
    "pg_temp_1",
    "pg_toast_temp_1",
    "information_schema",
    # PostgreSQL default databases
    "postgres",
    "template0",
    "template1",
    # Our own fixed schemas
    "auth",
    "admin",
    "tenant",
    "catalog",
    "orders",
    "system",
    "admin_api",
    "auth_api",
    "catalog_api",
    "orders_api",
}


class InvalidTenantSlug(ValueError):
    """Raised when a tenant slug fails validation."""


def validate_tenant_slug(slug: str) -> str:
    """Validate a tenant slug and return it unchanged if valid.

    Raises:
        InvalidTenantSlug: if slug does not match the pattern or is reserved.
    """
    if not isinstance(slug, str):
        raise InvalidTenantSlug(f"Slug must be a string, got {type(slug).__name__}")
    if not SLUG_PATTERN.match(slug):
        raise InvalidTenantSlug(
            f"Invalid slug: {slug!r}. Must match ^[a-z][a-z0-9_]{{2,40}}$"
        )
    if slug in RESERVED_SCHEMAS:
        raise InvalidTenantSlug(f"Reserved slug: {slug!r}")
    return slug