from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root_returns_api_message():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tell Your Story API"}


def test_start_returns_first_question():
    response = client.post("/interview/start")
    assert response.status_code == 200
    body = response.json()
    assert "first_question" in body
    assert isinstance(body["first_question"], str)
    assert body["first_question"].strip()
