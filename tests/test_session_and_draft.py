from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_start_includes_session_id():
    response = client.post("/interview/start")
    assert response.status_code == 200
    body = response.json()
    assert body.get("session_id")
    assert body.get("first_question")


def test_chat_persists_session_and_messages():
    start = client.post("/interview/start").json()
    session_id = start["session_id"]

    chat = client.post(
        "/interview/chat",
        json={
            "session_id": session_id,
            "user_text": "저는 어린 시절 바닷가에서 자랐습니다.",
            "conversation_history": [],
        },
    )
    assert chat.status_code == 200
    assert chat.json()["session_id"] == session_id

    saved = client.get(f"/interview/session/{session_id}")
    assert saved.status_code == 200
    data = saved.json()
    assert data["session_id"] == session_id
    assert len(data["messages"]) >= 2


def test_draft_generation_works_with_session_messages():
    start = client.post("/interview/start").json()
    session_id = start["session_id"]

    client.post(
        "/interview/chat",
        json={
            "session_id": session_id,
            "user_text": "힘들었지만 가족 덕분에 이겨냈습니다.",
            "conversation_history": [],
        },
    )

    draft = client.post("/interview/draft", json={"session_id": session_id})
    assert draft.status_code == 200
    body = draft.json()
    assert body["session_id"] == session_id
    assert isinstance(body.get("draft"), str)
    assert body["draft"].strip()
