# admin_api

LaunchPad SaaS control plane — manages tenants, client credentials, plans, subscriptions.

## Management API

Management endpoints are under `/api/v1` and require `Authorization: Bearer <JWT>`.
The token must be issued by `auth_api`, signed with the same `SECRET_KEY`, and
contain the boolean claim `is_superuser: true`. Valid user tokens without that
claim receive `403`; missing, invalid, or expired tokens receive `401`. Health
and root endpoints remain public.

The admin API does not require or inspect `X-Tenant-ID`, `X-Client-ID`, or
`X-Client-Secret`. It intentionally does not install tenant-isolation middleware:
superuser JWTs authorize platform-wide operations, independently of tenant
headers. The shared `require_auth` dependency parses `is_superuser` into
`AuthClaims`; `require_superuser` enforces it. The admin app supplies its
configured `SECRET_KEY` to that shared dependency.

| Resource | Endpoints |
| --- | --- |
| Tenants | `GET/POST /tenants`, `GET/PATCH/DELETE /tenants/{tenant_id}` |
| Credentials | `GET/POST /tenants/{tenant_id}/credentials`, `PATCH/DELETE /credentials/{credential_id}` |
| Plans | `GET/POST /plans`, `GET/PATCH/DELETE /plans/{plan_id}` |
| Subscriptions | `GET/POST /subscriptions`, `GET/PATCH/DELETE /subscriptions/{subscription_id}` |

Collection endpoints accept `offset` and `limit` (maximum `500`). Tenants and
subscriptions can also be filtered by status; plans accept `active`, and
subscriptions accept `tenant_id`. Tenant lists additionally accept `search`.
Tenant slugs are immutable after creation.
Creating a credential returns its generated `client_secret` once; only its
Argon2 hash is persisted. Deleting a credential revokes it rather than
physically removing its record. Duplicate or constraint-conflicting writes
return `409`, and missing resources return `404`.

## Application structure and writes

- `app/models/` contains SQLAlchemy table mappings.
- `app/schemas/` contains API request and response schemas.
- `app/services/` owns resource queries, transaction boundaries, and business rules.
- `app/api/` contains HTTP routing and dependency wiring; domain errors are mapped
  centrally to consistent `{"detail": ...}` responses.

Each request gets its own async SQLAlchemy session. Mutations run in an explicit
transaction; changes to existing rows use `SELECT ... FOR UPDATE`, and foreign
tenant/plan references are locked while creating credentials or creating and
changing subscriptions. Uniqueness and foreign-key conflicts map to `409`.

After a transaction commits, the service raises an in-process `AdminEvent` to
registered async handlers. Events include the resource snapshot but never
credential secrets or hashes. Handler failures are logged and do not turn an
already-committed API operation into a reported failure. This event bus is
process-local and is not durable or shared across workers.