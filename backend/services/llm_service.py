import asyncio
import json
import logging
from typing import Any

from openai import OpenAI

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("tell-your-story.llm")
client = None
if settings.provider_api_key:
    client = OpenAI(
        api_key=settings.provider_api_key,
        base_url=settings.openai_base_url,
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


def _limit_conversation_history(conversation_history: list[dict[str, str]]) -> list[dict[str, str]]:
    if settings.max_history_messages <= 0:
        return conversation_history
    return conversation_history[-settings.max_history_messages :]


def _create_chat_completion(messages: list[dict[str, str]]) -> Any:
    return client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        stream=False,
    )


def _parse_json_response(raw_content: str) -> dict[str, str]:
    cleaned = (raw_content or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


async def generate_interview_response(
    user_text: str,
    conversation_history: list[dict[str, str]],
    session_summary: str = "",
) -> dict[str, str]:
    normalized_user_text = user_text.strip()
    if not normalized_user_text:
        return {
            "reaction": "답변을 아직 듣지 못했습니다.",
            "next_question": "조금 더 자세히 말씀해주실 수 있을까요?",
        }

    if not client:
        return {
            "reaction": f"아, '{normalized_user_text}'라고 하셨군요. (API 키가 설정되지 않아 모의 응답을 보냅니다)",
            "next_question": "다음 질문은 무엇인가요?",
        }

    summary_context = session_summary.strip() or "아직 요약 없음"
    messages = [
        {
            "role": "system",
            "content": f"""
            당신은 어르신(60대 이상)의 자서전을 써드리기 위해 인터뷰를 진행하는 따뜻하고 예의 바른 'AI 작가'입니다.
            현재까지 대화 요약:
            {summary_context}

            목표:
            1. 답변에 공감하고 경청합니다.
            2. 구체적인 에피소드를 이끌어내는 꼬리 질문을 합니다.
            3. 한 번에 하나의 질문만 합니다.

            출력 형식(JSON):
            {{
                "reaction": "짧은 공감 멘트",
                "next_question": "다음 질문"
            }}
            반드시 JSON 형식으로만 응답하세요.
            """,
        }
    ]
    limited_history = _limit_conversation_history(conversation_history)
    messages.extend(_build_history_messages(limited_history))
    messages.append({"role": "user", "content": normalized_user_text})

    try:
        response = await asyncio.to_thread(_create_chat_completion, messages)
        content = _parse_json_response(response.choices[0].message.content or "")
        reaction = str(content.get("reaction", "")).strip()
        next_question = str(content.get("next_question", "")).strip()
        if not reaction or not next_question:
            raise ValueError("Model response does not include required fields.")
        return {"reaction": reaction, "next_question": next_question}
    except Exception as exc:
        logger.exception(
            "service_error error_type=provider service=llm operation=chat exception=%s",
            type(exc).__name__,
        )
        return {
            "reaction": "아, 그렇군요. 정말 소중한 이야기네요.",
            "next_question": "그 다음에는 어떤 일이 있었나요?",
        }


async def generate_session_summary(
    existing_summary: str,
    conversation_history: list[dict[str, str]],
) -> str:
    if not conversation_history:
        return existing_summary

    if not client:
        recent_text = " / ".join(msg.get("text", "") for msg in conversation_history[-6:] if msg.get("text"))
        fallback = f"{existing_summary} {recent_text}".strip()
        return fallback[-1200:]

    messages = [
        {
            "role": "system",
            "content": """
            당신은 인터뷰 기록 편집자입니다.
            기존 요약과 새 대화를 반영해 6~8문장 한국어 요약을 작성하세요.
            인물, 시기, 사건, 감정, 전환점을 담아주세요.
            """,
        },
        {"role": "user", "content": f"기존 요약:\n{existing_summary or '(없음)'}"},
        {"role": "user", "content": f"새 대화:\n{json.dumps(conversation_history[-12:], ensure_ascii=False)}"},
    ]
    try:
        response = await asyncio.to_thread(_create_chat_completion, messages)
        summary = (response.choices[0].message.content or "").strip()
        return summary or existing_summary
    except Exception as exc:
        logger.exception(
            "service_error error_type=provider service=llm operation=summary exception=%s",
            type(exc).__name__,
        )
        return existing_summary


async def generate_autobiography_draft(session_summary: str, messages: list[dict[str, str]]) -> str:
    if not client:
        fallback_lines = ["[자서전 초안 - 임시]", "", "요약:", session_summary or "요약 정보가 없습니다.", "", "대화 발췌:"]
        for msg in messages[-10:]:
            role = "나" if msg.get("role") == "user" else "AI"
            fallback_lines.append(f"- {role}: {msg.get('text', '')}")
        return "\n".join(fallback_lines)

    prompt_messages = [
        {
            "role": "system",
            "content": """
            당신은 구술 기록을 자서전 초안으로 정리하는 작가입니다.
            아래 자료를 바탕으로 한국어 초안을 작성하세요.
            구성: 1) 어린 시절 2) 전환점 3) 삶의 교훈
            문체는 따뜻하고 사실 중심으로 작성하세요.
            """,
        },
        {"role": "user", "content": f"세션 요약:\n{session_summary or '(없음)'}"},
        {"role": "user", "content": f"대화 기록:\n{json.dumps(messages[-24:], ensure_ascii=False)}"},
    ]
    try:
        response = await asyncio.to_thread(_create_chat_completion, prompt_messages)
        draft = (response.choices[0].message.content or "").strip()
        if not draft:
            raise ValueError("Empty draft response")
        return draft
    except Exception as exc:
        logger.exception(
            "service_error error_type=provider service=llm operation=draft exception=%s",
            type(exc).__name__,
        )
        return "[초안 생성에 실패했습니다. 잠시 후 다시 시도해주세요.]"
