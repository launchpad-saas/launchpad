from uuid import uuid4
from launchpad_shared import (
    BaseSchema, create_access_token, decode_access_token,
    hash_password, verify_password, build_fdw_setup_sql,
)

class T(BaseSchema):
    tenant_id: str
    full_name: str

assert T(tenant_id="x", full_name="Alice").model_dump(by_alias=True, mode="json") == {
    "tenantId": "x", "fullName": "Alice"
}

tid = uuid4()
token = create_access_token(subject="u1", tenant_id=tid, roles=["admin"], secret_key="test")
p = decode_access_token(token, secret_key="test")
assert p["sub"] == "u1" and p["tenant_id"] == str(tid) and p["roles"] == ["admin"]

h = hash_password("Secret123!")
assert verify_password("Secret123!", h) and not verify_password("nope", h)

sql = build_fdw_setup_sql(core_host="core_db", core_port=5432, core_db="launchpad_core", core_user="ro", core_password="pw")
assert "postgres_fdw" in sql and "foreign_users" in sql and "hashed_password" not in sql

print("ALL SMOKE TESTS OK")
