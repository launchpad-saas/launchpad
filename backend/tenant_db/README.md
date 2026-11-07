# tenant_db

Shared PostgreSQL database hosting **one schema per tenant**.

- Database: `launchpad_tenant`
- Schemas: `acme`, `xyz`, etc. (named after tenant slug)
- Each schema contains: `categories`, `products`, `orders`, `order_items`

## Why one DB, one schema per tenant?

- **Cost**: 10–20× cheaper than database-per-tenant at scale
- **Isolation**: Schemas are namespace-isolated — a tenant cannot see another's tables
- **Migrations**: One `ALTER TABLE` per schema via loop — simpler than N databases

## Schema naming rules

- Must match `^[a-z][a-z0-9_]{2,40}$`
- Blocked names: `public`, `pg_catalog`, `information_schema`, `auth`, `admin`, `tenant`
- Immutable after tenant is created (enforced in `admin_api`)