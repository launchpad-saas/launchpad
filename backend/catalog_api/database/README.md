# catalog_api — database

Owned by `backend/catalog_api`. Contains:

- `init-scripts/` — SQL executed on **first** Postgres container boot
  (`/docker-entrypoint-initdb.d`). Idempotent (`IF NOT EXISTS`).
- `seeds/` — dev/staging fixture data (NOT run automatically).

## Schema ownership

The `launchpad_catalog` database is owned exclusively by `catalog_api`.
Alembic migrations (`backend/catalog_api/alembic/versions/`) are the source
of truth for table definitions.

## Reset

    docker compose down -v
    docker compose up -d