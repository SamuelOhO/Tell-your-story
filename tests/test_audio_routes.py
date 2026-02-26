from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import interview


client = TestClient(app)


def test_stt_route_returns_text_when_service_succeeds(monkeypatch):
    async def fake_transcribe_audio(file_path: str) -> str:
        return "음성 인식 결과"

    monkeypatch.setattr(interview, "transcribe_audio", fake_transcribe_audio)

    files = {"file": ("sample.webm", b"fake-audio", "audio/webm")}
    response = client.post("/interview/stt", files=files)
    assert response.status_code == 200
    assert response.json()["text"] == "음성 인식 결과"


def test_tts_route_returns_audio_url_when_service_succeeds(monkeypatch):
    async def fake_generate_audio(text: str, output_path: str):
        Path(output_path).write_bytes(b"ID3")
        return output_path

    monkeypatch.setattr(interview, "generate_audio", fake_generate_audio)

    response = client.post("/interview/tts", json={"text": "안녕하세요"})
    assert response.status_code == 200
    assert response.json()["audio_url"].startswith("/static/tts_")
