CREATE EXTENSION IF NOT EXISTS postgres_fdw;

CREATE SERVER IF NOT EXISTS launchpad_core_server
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'core_db', port '5432', dbname 'launchpad_core');

CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER
    SERVER launchpad_core_server
    OPTIONS (user 'user', password 'pass');

CREATE FOREIGN TABLE IF NOT EXISTS foreign_users (
    id UUID,
    tenant_id UUID,
    email TEXT,
    full_name TEXT,
    is_active BOOLEAN
) SERVER launchpad_core_server
OPTIONS (schema_name 'public', table_name 'users');