from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_no_tenant():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_with_tenant():
    r = client.get("/api/v1/health", headers={"X-Tenant-ID": "11111111-1111-1111-1111-111111111111"})
    assert r.status_code == 200
    assert r.json()["tenantId"] == "11111111-1111-1111-1111-111111111111"