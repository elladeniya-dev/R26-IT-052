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


def test_score_products_returns_scores_with_taxonomy_version(client):
    body = {"products": [{"id": "a", "title": "Floral Midi Dress", "category": "dress", "colors": ["beige"]}]}
    r = client.post("/api/v1/trends/score-products", json=body)
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        out = r.json()
        assert out["data"][0]["id"] == "a"
        assert "trend_score" in out["data"][0] and "matches" in out["data"][0]
        assert out["meta"]["taxonomy_version"] and out["meta"]["products"] == 1


def test_score_products_rejects_oversized_batches(client):
    body = {"products": [{"id": str(i)} for i in range(501)]}
    assert client.post("/api/v1/trends/score-products", json=body).status_code == 422


def test_unsupported_horizon_is_a_validation_error_not_a_missing_snapshot(client):
    for path in ("/api/v1/trends?horizon=4", "/api/v1/trends/meta?horizon=7", "/api/v1/trends/color?horizon=1",
                 "/api/v1/trends/products?horizon=9"):
        assert client.get(path).status_code == 422, path
    r = client.post("/api/v1/trends/score-products", json={"products": [], "horizon": 4})
    assert r.status_code == 422


def test_unknown_confidence_filter_is_rejected(client):
    assert client.get("/api/v1/trends?min_confidence=banana").status_code == 422


def test_supported_horizons_and_confidences_are_still_accepted(client):
    # The validation above must not reject the values the app actually sends.
    for path in ("/api/v1/trends?horizon=3", "/api/v1/trends?horizon=5&min_confidence=high",
                 "/api/v1/trends/meta?horizon=3", "/api/v1/trends/color?horizon=5"):
        assert client.get(path).status_code != 422, path


def test_stats_attribute_type_is_validated_not_a_server_error(client):
    assert client.get("/api/v1/stats/attributes/not-a-type").status_code == 422
    assert client.get("/api/v1/stats/attributes/color").status_code == 200


def test_nul_characters_are_a_clean_400_not_a_server_error(client):
    # Postgres cannot store NUL; psycopg used to raise and the caller saw a 500.
    for path in ("/api/v1/products/%00", "/api/v1/products?brand=%00", "/api/v1/brands/%00/coverage",
                 "/api/v1/trends/segments?segment_type=%00"):
        r = client.get(path)
        assert r.status_code == 400, path
        assert r.json()["error"]["code"] == "BAD_REQUEST"


def test_database_outage_is_a_retryable_503_with_the_error_envelope():
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import OperationalError

    from app.database import get_db
    from app.main import app

    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = broken_db
    try:
        r = TestClient(app).get("/api/v1/trends/segments")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


def test_unexpected_errors_use_the_error_envelope():
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    def explode():
        raise RuntimeError("boom")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = explode
    try:
        r = TestClient(app, raise_server_exceptions=False).get("/api/v1/trends/segments")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "boom" not in r.text   # internals are logged, not leaked


def test_model_and_env_paths_do_not_depend_on_the_working_directory():
    from pathlib import Path

    from app.config import ENV_FILE
    from app.ml.engine import DEFAULT_TRENDNET_PATH, TrendEngine

    assert Path(DEFAULT_TRENDNET_PATH).is_absolute() and Path(DEFAULT_TRENDNET_PATH).exists()
    assert ENV_FILE.is_absolute()
    # The engine must load the real model by default, not silently fall back to MRTF only.
    assert TrendEngine().model_name == "trendnet+mrtf"
