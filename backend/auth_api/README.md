# auth_api

LaunchPad authentication and account management.

## Database

Apply migrations before starting the API:

```powershell
alembic upgrade head
```

Create the first platform owner interactively (passwords are not placed on the
command line):

```powershell
python scripts/create_superuser.py
```

The bootstrap user has no tenant and is created outside public registration.
Admin user creation and privilege changes require an existing superuser JWT.

## Endpoints

- `POST /api/v1/users/signup` — tenant-scoped public registration. Requires a
  valid `X-Tenant-ID`; the new account is unverified until the emailed link is
  redeemed.
- `POST /api/v1/login/access-token` — OAuth2 form login (`username`, `password`).
  Also requires tenant context for tenant users; platform users log in without it.
- `POST /api/v1/login/refresh` — rotates refresh tokens; refresh tokens are
  stored hashed and reuse revokes the whole token family.
- `POST /api/v1/login/logout` and `/api/v1/login/logout-all` — revoke one or all
  refresh sessions. Current access tokens are also checked against their session.
- `POST /api/v1/verify-email`, `/api/v1/resend-verification`,
  `/api/v1/password-recovery/{email}`, and `/api/v1/reset-password/` — single-use,
  expiring email verification and password reset flows.
- `GET/PATCH/DELETE /api/v1/users/me` and `PATCH /api/v1/users/me/password` —
  profile, account, and password operations.
- `/api/v1/users/` and `/api/v1/users/{user_id}` — superuser-only user
  administration. Passwords and hashes are never returned.

`X-Tenant-ID` is the UUID of the tenant context; it is not an authentication
secret. Tenant existence is owned by `admin_api` and is a soft reference in this
database. Set `SECRET_KEY` identically in `auth_api` and `admin_api`.

Email verification and password recovery require SMTP configuration. Configure
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`,
`SMTP_USE_TLS`, and `FRONTEND_URL`. Email delivery is not simulated when SMTP is
missing; the API reports `503`. The token hashes are persisted, never the raw
tokens.

Login attempts are recorded in `login_attempts` and throttled by account/IP.
`auth_tokens` stores only hashed, expiring, single-use verification/reset
tokens. `sessions` stores hashed refresh tokens and rotation-family metadata.