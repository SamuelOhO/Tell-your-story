from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_chat_accepts_valid_payload():
    payload = {
        "user_text": "저는 부산에서 자랐습니다.",
        "conversation_history": [
            {"role": "user", "text": "안녕하세요"},
            {"role": "ai", "text": "반갑습니다. 어린 시절 이야기를 들려주세요."},
        ],
    }

    response = client.post("/interview/chat", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "ai_text" in body
    assert "next_question" in body


def test_chat_rejects_invalid_history_payload():
    payload = {
        "user_text": "정상 문장",
        "conversation_history": [{"role": "user"}],
    }

    response = client.post("/interview/chat", json=payload)
    assert response.status_code == 422


def test_chat_rejects_blank_user_text():
    payload = {
        "user_text": "   ",
        "conversation_history": [],
    }

    response = client.post("/interview/chat", json=payload)
    assert response.status_code == 422
