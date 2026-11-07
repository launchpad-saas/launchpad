-- Shared tenant database
-- The `acme` schema is created here so Phase 3.2.7 migrations can run
-- against a real tenant before the full onboarding flow (Phase 3.4) exists.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dev tenant: acme (must match regex ^[a-z][a-z0-9_]{2,40}$)
CREATE SCHEMA IF NOT EXISTS acme;