from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "corp-ext"


def test_metrics() -> None:
    response = TestClient(create_app()).get("/metrics")
    assert response.status_code == 200
    assert "python_info" in response.text


def test_docs_hidden_in_prod() -> None:
    prod = TestClient(create_app(Settings(env="prod")))
    assert prod.get("/corp/api/openapi.json").status_code == 404
    dev = TestClient(create_app(Settings(env="dev")))
    assert dev.get("/corp/api/openapi.json").status_code == 200
