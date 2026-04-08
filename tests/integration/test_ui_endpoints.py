def test_optional_ui_route_is_available(client):
    response = client.get("/ui")

    assert response.status_code == 200
    body = response.text
    assert "Smart Document QA Console" in body
    assert "optional" in body.lower()
    assert "API server is the primary interface" in body


def test_ui_docs_route_is_available(client):
    response = client.get("/ui/docs")

    assert response.status_code == 200
    body = response.text
    assert "Component Documentation" in body
    assert "Where: src/app/api" in body
    assert "API-first design" in body


def test_favicon_route_is_quiet(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 204
