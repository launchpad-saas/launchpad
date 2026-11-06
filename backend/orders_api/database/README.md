# orders_api — database

Owned by `backend/orders_api`. Contains:

- `init-scripts/` — SQL executed on **first** Postgres container boot
  (`/docker-entrypoint-initdb.d`). Idempotent (`IF NOT EXISTS`).
- `seeds/` — dev/staging fixture data (NOT run automatically).

## Schema ownership

The `launchpad_orders` database is owned exclusively by `orders_api`.
Alembic migrations (`backend/orders_api/alembic/versions/`) are the source
of truth for table definitions.

## Reset

    docker compose down -v
    docker compose up -d