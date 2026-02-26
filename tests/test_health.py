from fastapi.testclient import TestClient

from backend import main as main_module
from backend.main import app


client = TestClient(app)


def test_health_ok_when_db_is_available(monkeypatch):
    monkeypatch.setattr(main_module, "check_db_health", lambda: (True, "ok"))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "up", "db": "up"}


def test_health_degraded_when_db_is_unavailable(monkeypatch):
    monkeypatch.setattr(main_module, "check_db_health", lambda: (False, "database locked"))
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["db"] == "down"
