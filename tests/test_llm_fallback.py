from fastapi.testclient import TestClient

from backend.main import app
from backend.services import llm_service


client = TestClient(app)


def test_chat_returns_mock_message_when_client_is_missing(monkeypatch):
    monkeypatch.setattr(llm_service, "client", None)

    payload = {
        "user_text": "저는 바다를 좋아합니다.",
        "conversation_history": [
            {"role": "user", "text": "안녕하세요"},
            {"role": "ai", "text": "반갑습니다. 기억나는 바다 이야기가 있나요?"},
        ],
    }

    response = client.post("/interview/chat", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "모의 응답" in body["ai_text"]
    assert body["next_question"]
