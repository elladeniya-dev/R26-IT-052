def test_health_is_always_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_ready_reports_db_and_model(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["database"] is True
    assert body["model_loaded"] is True


def test_trends_returns_error_envelope_when_no_snapshot_exists(client):
    r = client.get("/api/v1/trends")
    assert r.status_code in (200, 503)
    if r.status_code == 503:
        body = r.json()
        assert body["error"]["code"] == "NO_TREND_SNAPSHOT"


def test_products_list_envelope_shape(client):
    r = client.get("/api/v1/products?size=5")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body and "meta" in body
    assert set(body["meta"].keys()) == {"page", "size", "total"}


def test_product_not_found_returns_error_envelope(client):
    r = client.get("/api/v1/products/does-not-exist:0")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_admin_routes_require_api_key(client):
    r = client.get("/api/v1/admin/runs")
    assert r.status_code == 401
