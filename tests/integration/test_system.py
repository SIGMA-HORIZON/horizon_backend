"""Tests d'intégration — routes système (/health, /, OpenAPI)."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "email_mode" in body


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "api/v1" in resp.json()["message"].lower() or "/api/v1" in resp.json()["message"]


def test_openapi_tags(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    tags = {t["name"] for t in spec.get("tags", [])}
    # Au moins les domaines métier présents dans la spec
    paths = spec.get("paths", {})
    assert any(p.startswith("/api/v1/") for p in paths)
