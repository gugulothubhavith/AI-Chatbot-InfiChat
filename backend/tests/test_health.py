"""Health endpoint tests — validates basic app startup and routing."""


def test_health_endpoint(client):
    """GET /health should return 200 with status info."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")


def test_root_endpoint(client):
    """GET / should return welcome message."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "InfiChat" in data["message"]


def test_openapi_available(client):
    """OpenAPI schema should be accessible."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "info" in data


def test_cors_headers(client):
    """CORS headers should be present on cross-origin requests."""
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"
