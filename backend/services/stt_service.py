import logging

from openai import OpenAI
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("tell-your-story.stt")
client = None
if settings.provider_api_key:
    client = OpenAI(api_key=settings.provider_api_key, base_url=settings.openai_base_url)

async def transcribe_audio(file_path: str) -> str:
    if not client:
        return ""

    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="ko"
            )
        return transcript.text
    except Exception as exc:
        logger.exception(
            "service_error error_type=provider service=stt operation=transcribe exception=%s",
            type(exc).__name__,
        )
        return ""
