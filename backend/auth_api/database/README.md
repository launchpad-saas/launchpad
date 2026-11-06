# auth_api — database

Owned by `backend/auth_api`. Contains:

- `init-scripts/` — SQL executed on **first** Postgres container boot
  (`/docker-entrypoint-initdb.d`). Idempotent (`IF NOT EXISTS`).
- `seeds/` — dev/staging fixture data (NOT run automatically).

## Schema ownership

The `launchpad_auth` database is owned exclusively by `auth_api`.
Alembic migrations (`backend/auth_api/alembic/versions/`) are the source
of truth for table definitions.

## Reset

    docker compose down -v
    docker compose up -d