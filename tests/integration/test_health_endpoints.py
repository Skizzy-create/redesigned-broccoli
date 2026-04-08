from uuid import UUID


def test_health_endpoint_returns_success_envelope(client, auth_headers):
    response = client.get("/api/v1/health", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["healthy"] is True
    assert payload["data"]["service"] == "Smart Document Q&A API"
    assert "meta" in payload
    assert payload["meta"]["request_id"] == response.headers["X-Request-ID"]


def test_health_endpoint_generates_valid_request_id(client, auth_headers):
    response = client.get("/api/v1/health", headers=auth_headers)

    request_id = response.headers["X-Request-ID"]
    parsed = UUID(request_id)
    assert str(parsed) == request_id


def test_health_endpoint_respects_client_request_id(client, auth_headers):
    request_id = "custom-request-id-123"
    headers = {"X-Request-ID": request_id, **auth_headers}
    response = client.get("/api/v1/health", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["meta"]["request_id"] == request_id


def test_readiness_endpoint_reports_ready(client, auth_headers):
    response = client.get("/api/v1/health/ready", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["ready"] is True


def test_openapi_and_docs_are_exposed(client):
    openapi = client.get("/openapi.json")
    docs = client.get("/docs")

    assert openapi.status_code == 200
    assert docs.status_code == 200
    assert openapi.json()["info"]["title"] == "Smart Document Q&A API"


def test_unknown_route_returns_404(client):
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404


def test_protected_endpoint_rejects_missing_api_key(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 401
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["message"] == "Missing X-API-Key header."


def test_protected_endpoint_rejects_invalid_api_key(client):
    response = client.get("/api/v1/health", headers={"X-API-Key": "bad-key"})

    assert response.status_code == 401
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["message"] == "Invalid API key."
