# LaunchPad — Multi-Tenant SaaS E-Commerce Platform

A production-grade, multi-tenant SaaS e-commerce backend built with FastAPI, PostgreSQL, and Docker Compose.

## Architecture Overview

**4 independent microservices, each with its own database:**

| Service | Port | Database | Purpose |
|---|---|---|---|
| `admin_api` | 8000 | `launchpad_admin` | SaaS control plane — tenants, credentials, plans, subscriptions |
| `auth_api` | 8001 | `launchpad_auth` | User authentication — register, login, JWT, sessions |
| `catalog_api` | 8002 | `launchpad_catalog` | Products and categories (per-tenant) |
| `orders_api` | 8003 | `launchpad_orders` | Orders and cart (per-tenant) |

**Each service owns:**
- Its own PostgreSQL database
- Its own SQLAlchemy models (`app/models/`)
- Its own Alembic migrations (`alembic/versions/`)
- Its own Docker Compose file
- Its own database init scripts (`database/init-scripts/`)

## Quick Start

### Prerequisites

- **Docker Desktop** (WSL2 backend on Windows)
- **Git**
- **PowerShell** (Windows) or Bash (macOS/Linux)

### Clone and Run

```bash
git clone https://github.com/launchpad-saas/launchpad.git
cd launchpad
```

**Windows:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\up.ps1
```

**macOS/Linux:**

```bash
cp .env.example .env
docker compose up -d --build
```

Wait ~2 minutes. Then verify all 4 services:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8001/api/v1/health
Invoke-RestMethod http://localhost:8002/api/v1/health
Invoke-RestMethod http://localhost:8003/api/v1/health
```

All four should return `status: ok`.

## Running Migrations

**Always run migrations from inside the service folder** — Docker Compose `include:` does NOT propagate overrides to `run` commands:

```powershell
cd backend\admin_api
docker compose -p launchpad run --rm admin_api alembic upgrade head
cd ..\..
```

Repeat for `auth_api`, `catalog_api`, `orders_api`.

Or use: `.\scripts\migrate-all.ps1`

## Creating New Migrations

```powershell
cd backend\<service>
docker compose -p launchpad run --rm <service> alembic revision --autogenerate -m "description"
docker compose -p launchpad run --rm <service> alembic upgrade head
cd ..\..
```

## Project Structure

```
launchpad/
├── compose.yml
├── .env.example
├── backend/
│   ├── admin_api/      → port 8000, DB launchpad_admin
│   ├── auth_api/       → port 8001, DB launchpad_auth
│   ├── catalog_api/    → port 8002, DB launchpad_catalog
│   └── orders_api/     → port 8003, DB launchpad_orders
├── packages/
│   └── launchpad_shared/  (BaseSchema, TenantMiddleware, JWT)
├── scripts/  (up.ps1, down.ps1, reset.ps1, migrate-all.ps1)
├── frontend/  (Phase 4)
├── infra/     (Phase 5)
└── docs/
```

## Database Schema

### `launchpad_admin`
| Table | Purpose |
|---|---|
| `tenants` | SaaS customers (companies) |
| `client_credentials` | API keys per tenant (bcrypt-hashed) |
| `plans` | Free / Pro / Enterprise tiers |
| `subscriptions` | Tenant → plan bindings + billing state |

### `launchpad_auth`
| Table | Purpose |
|---|---|
| `users` | End-user accounts (unique on tenant_id + email) |
| `sessions` | Refresh token rotation |

### `launchpad_catalog` *(Phase 3.2.7)*
| Table | Purpose |
|---|---|
| `products` | Tenant products |
| `categories` | Product categories |

### `launchpad_orders` *(Phase 3.2.7)*
| Table | Purpose |
|---|---|
| `orders` | Customer orders |
| `order_items` | Line items per order |

## Multi-Tenancy Model

**Per-tenant database isolation.**

When you onboard a new tenant (Phase 3.4), the system:
1. Creates a row in `launchpad_admin.tenants`
2. Generates `client_id` + `client_secret` (stored hashed)
3. Creates `tenant_<slug>_catalog` and `tenant_<slug>_orders` databases
4. Runs tenant schema migrations
5. Returns credentials **once** to the SaaS owner

**Every API request carries:**

```
X-Tenant-ID: abc-123-uuid
X-Client-ID: lp_live_abc123
X-Client-Secret: sk_live_xyz789
Authorization: Bearer <user-jwt>
```

**Middleware chain:**
1. `TenantMiddleware` — validates X-Tenant-ID as UUID
2. `ClientAuthMiddleware` — validates X-Client-ID/Secret *(Phase 3.5)*
3. `JWTAuthMiddleware` — validates Bearer token, sets request.state.user_id
4. Router — queries the tenant's database

## Coding Standards

See `copilot-instructions.md`. Key rules:
- **Architecture**: Pragmatic DDD — `domain/`, `app/`, `infra/`, `api/`. Routers stay thin.
- **Schemas**: Inherit from `BaseSchema` — snake_case internally, camelCase JSON
- **Database**: Singular ORM names, snake_case tables, UUIDs, UTC timestamps
- **Testing**: Add tests for new behavior; run in Docker Compose
- **CI**: GitHub Actions runs tests across all 4 services

## Development Workflow

**Start stack:** `.\scripts\up.ps1`

**Watch logs:** `docker compose logs -f admin_api`

**Run tests:**
```powershell
cd backend\admin_api
docker compose -p launchpad run --rm admin_api pytest
cd ..\..
```

**Rebuild one service:** `docker compose build admin_api` then `docker compose up -d admin_api`

**Stop:** `.\scripts\down.ps1`

**Full reset (destroys data):** `.\scripts\reset.ps1`

## Roadmap

- [x] **Phase 1** — Baseline Docker Compose
- [x] **Phase 2** — `launchpad_shared` (BaseSchema, TenantMiddleware, JWT, FDW helper)
- [x] **Phase 3.1** — 3 microservices split (core, catalog, orders)
- [x] **Phase 3.2** — Split core → `admin_api` + `auth_api`, real models, migrations applied
- [ ] **Phase 3.2.7** — Product, Category, Order, OrderItem models + migrations
- [ ] **Phase 3.3** — Auth endpoints (register, login, refresh)
- [ ] **Phase 3.4** — Tenant onboarding API (creates DB, generates credentials)
- [ ] **Phase 3.5** — ClientAuthMiddleware (X-Client-ID/Secret validation)
- [ ] **Phase 3.6** — Subscription enforcement + Stripe webhook
- [ ] **Phase 3.7** — End-to-end test: onboard 2 tenants, verify isolation
- [ ] **Phase 4** — Frontend: platform-admin + storefront
- [ ] **Phase 5** — Kustomize + Azure Bicep
- [ ] **Phase 6** — CI/CD pipeline

## Troubleshooting

### Port conflicts
```powershell
docker ps -a --filter "name=launchpad-"
docker rm -f <conflicting-container>
```

### Migration errors ("Target database is not up to date")
If `alembic_version` is stale but tables exist:
```powershell
cd backend\<service>
docker compose -p launchpad run --rm <service> alembic stamp head
cd ..\..
```

### Migration file not appearing
**Always run migrations from inside the service folder** — Docker Compose `include:` does not propagate overrides to `run` commands.

### Volume loss after `docker compose down -v`
`-v` deletes all database volumes. Use plain `docker compose down` to preserve.

## License

See `LICENSE`.
