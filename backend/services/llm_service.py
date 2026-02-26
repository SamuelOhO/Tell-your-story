import asyncio
import json
import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("UPSTAGE_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
client = None
if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

def _build_history_messages(conversation_history: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for msg in conversation_history:
        if not isinstance(msg, dict):
            continue

        text = str(msg.get("text", "")).strip()
        if not text:
            continue

        raw_role = str(msg.get("role", "")).strip().lower()
        role = "user" if raw_role == "user" else "assistant"
        messages.append({"role": role, "content": text})

    return messages


def _create_chat_completion(messages: list[dict[str, str]]) -> Any:
    return client.chat.completions.create(
        model="solar-pro2",
        messages=messages,
        stream=False,
    )


def _parse_model_response(raw_content: str) -> dict[str, str]:
    cleaned = (raw_content or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    content = json.loads(cleaned)
    reaction = str(content.get("reaction", "")).strip()
    next_question = str(content.get("next_question", "")).strip()

    if not reaction or not next_question:
        raise ValueError("Model response does not include required fields.")

    return {"reaction": reaction, "next_question": next_question}


async def generate_interview_response(user_text: str, conversation_history: list[dict[str, str]]) -> dict[str, str]:
    normalized_user_text = user_text.strip()
    if not normalized_user_text:
        return {
            "reaction": "답변을 아직 듣지 못했습니다.",
            "next_question": "조금 더 자세히 말씀해주실 수 있을까요?",
        }

    if not client:
        return {
            "reaction": f"아, '{normalized_user_text}'라고 하셨군요. (API 키가 설정되지 않아 모의 응답을 보냅니다)",
            "next_question": "다음 질문은 무엇인가요?"
        }

    messages = [
        {"role": "system", "content": """
        당신은 어르신(60대 이상)의 자서전을 써드리기 위해 인터뷰를 진행하는 따뜻하고 예의 바른 'AI 작가'입니다.

        목표:
        1. 어르신이 편안하게 옛 이야기를 꺼낼 수 있도록 공감하고 경청합니다.
        2. 답변을 바탕으로 구체적인 에피소드를 이끌어낼 수 있는 '꼬리물기 질문'을 합니다.
        3. 한 번에 하나의 질문만 합니다.
        4. 말투는 정중하고 따뜻하게 합니다 (예: ~하셨군요, 정말 대단하시네요).

        출력 형식 (JSON):
        {
            "reaction": "어르신의 말에 대한 짧은 리액션 및 공감 멘트",
            "next_question": "다음 질문"
        }
        반드시 JSON 형식으로만 응답해주세요.
        """}
    ]
    messages.extend(_build_history_messages(conversation_history))
    messages.append({"role": "user", "content": normalized_user_text})

    try:
        response = await asyncio.to_thread(_create_chat_completion, messages)
        raw_content = response.choices[0].message.content or ""
        return _parse_model_response(raw_content)
    except Exception as e:
        print(f"Error in LLM: {type(e).__name__}")
        return {
            "reaction": "아, 그렇군요. 정말 소중한 이야기네요.",
            "next_question": "그 다음에는 어떤 일이 있었나요?"
        }
