from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal
from ..services.llm_service import generate_interview_response

router = APIRouter()

class ChatMessage(BaseModel):
    role: Literal["user", "ai", "assistant"]
    text: str = Field(min_length=1)

class ChatRequest(BaseModel):
    user_text: str = Field(min_length=1)
    conversation_history: list[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    ai_text: str
    next_question: str

@router.post("/start")
async def start_interview():
    return {"message": "Interview started", "first_question": "어린 시절 가장 기억에 남는 추억은 무엇인가요?"}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    history = [{"role": msg.role, "text": msg.text} for msg in request.conversation_history]
    response = await generate_interview_response(request.user_text, history)

    return ChatResponse(
        ai_text=response.get("reaction", ""),
        next_question=response.get("next_question", ""),
    )
