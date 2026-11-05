"""PostgreSQL FDW helpers for cross-DB user reads."""

CORE_SERVER_NAME = "launchpad_core_server"

FOREIGN_USERS_COLUMNS = [
    "id UUID",
    "tenant_id UUID",
    "email TEXT",
    "full_name TEXT",
    "is_active BOOLEAN",
]


def build_fdw_setup_sql(
    *,
    core_host: str,
    core_port: int,
    core_db: str,
    core_user: str,
    core_password: str,
) -> str:
    columns_sql = ",\n    ".join(FOREIGN_USERS_COLUMNS)
    return f"""
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

CREATE SERVER IF NOT EXISTS {CORE_SERVER_NAME}
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host '{core_host}', port '{core_port}', dbname '{core_db}');

CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER
    SERVER {CORE_SERVER_NAME}
    OPTIONS (user '{core_user}', password '{core_password}');

CREATE FOREIGN TABLE IF NOT EXISTS foreign_users (
    {columns_sql}
) SERVER {CORE_SERVER_NAME}
OPTIONS (schema_name 'public', table_name 'users');
""".strip()
