from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, StringConstraints

from ..config import get_settings
from ..services.llm_service import (
    generate_autobiography_draft,
    generate_interview_response,
    generate_session_summary,
)
from ..services.session_store import (
    append_message,
    count_messages,
    create_session,
    ensure_session,
    get_latest_draft,
    get_summary,
    list_messages,
    list_recent_messages,
    save_draft,
    session_exists,
    update_summary,
)
from ..services.stt_service import transcribe_audio
from ..services.tts_service import generate_audio

router = APIRouter()
settings = get_settings()
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
static_dir = Path(__file__).resolve().parents[1] / "static"
static_dir.mkdir(exist_ok=True)


class ChatMessage(BaseModel):
    role: Literal["user", "ai", "assistant"]
    text: NonEmptyText


class ChatRequest(BaseModel):
    user_text: NonEmptyText
    session_id: str | None = None
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    ai_text: str
    next_question: str
    summary_updated: bool = False


class StartResponse(BaseModel):
    message: str
    session_id: str
    first_question: str


class SessionResponse(BaseModel):
    session_id: str
    summary: str
    messages: list[ChatMessage]


class TtsRequest(BaseModel):
    text: NonEmptyText


class DraftRequest(BaseModel):
    session_id: str


@router.post("/start", response_model=StartResponse)
async def start_interview():
    session_id = create_session()
    return StartResponse(
        message="Interview started",
        session_id=session_id,
        first_question="어린 시절 가장 기억에 남는 추억은 무엇인가요?",
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    messages = list_messages(session_id)
    return SessionResponse(
        session_id=session_id,
        summary=get_summary(session_id),
        messages=[ChatMessage(role=msg["role"], text=msg["text"]) for msg in messages],
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = ensure_session(request.session_id)

    # Migration path: accept client-side history for first call in old clients.
    existing_messages = list_messages(session_id)
    if not existing_messages and request.conversation_history:
        for msg in request.conversation_history:
            role = "assistant" if msg.role in {"ai", "assistant"} else "user"
            append_message(session_id, role, msg.text)

    session_summary = get_summary(session_id)
    history = list_recent_messages(session_id, settings.max_history_messages)
    response = await generate_interview_response(request.user_text, history, session_summary)

    append_message(session_id, "user", request.user_text)
    append_message(session_id, "assistant", response.get("reaction", ""))

    summary_updated = False
    if settings.summary_update_every > 0 and count_messages(session_id) % settings.summary_update_every == 0:
        updated = await generate_session_summary(session_summary, list_messages(session_id))
        if updated.strip() and updated != session_summary:
            update_summary(session_id, updated)
            summary_updated = True

    return ChatResponse(
        session_id=session_id,
        ai_text=response.get("reaction", ""),
        next_question=response.get("next_question", ""),
        summary_updated=summary_updated,
    )


@router.post("/stt")
async def stt(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    temp_path = static_dir / f"stt_{uuid4().hex}{suffix}"

    content = await file.read()
    temp_path.write_bytes(content)

    try:
        text = await transcribe_audio(str(temp_path))
    finally:
        if temp_path.exists():
            temp_path.unlink()

    if not text:
        raise HTTPException(status_code=503, detail="음성 인식 서비스를 사용할 수 없습니다.")

    return {"text": text}


@router.post("/tts")
async def tts(request: TtsRequest):
    filename = f"tts_{uuid4().hex}.mp3"
    output_path = static_dir / filename
    generated = await generate_audio(request.text, str(output_path))
    if not generated:
        raise HTTPException(status_code=503, detail="음성 합성 서비스를 사용할 수 없습니다.")
    return {"audio_url": f"/static/{filename}"}


@router.post("/draft")
async def create_draft(request: DraftRequest):
    session_id = request.session_id
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    messages = list_messages(session_id)
    if not messages:
        raise HTTPException(status_code=400, detail="대화 기록이 없어 초안을 생성할 수 없습니다.")

    summary = get_summary(session_id)
    draft = await generate_autobiography_draft(summary, messages)
    save_draft(session_id, draft)
    return {"session_id": session_id, "draft": draft}


@router.get("/draft/latest/{session_id}")
async def latest_draft(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    draft = get_latest_draft(session_id)
    if not draft:
        raise HTTPException(status_code=404, detail="아직 생성된 초안이 없습니다.")
    return {"session_id": session_id, "draft": draft}
