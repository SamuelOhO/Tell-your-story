import logging

from openai import OpenAI
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("tell-your-story.tts")
client = None
if settings.provider_api_key:
    client = OpenAI(api_key=settings.provider_api_key, base_url=settings.openai_base_url)

async def generate_audio(text: str, output_path: str):
    if not client:
        return None

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(output_path)
        return output_path
    except Exception as exc:
        logger.exception(
            "service_error error_type=provider service=tts operation=synthesize exception=%s",
            type(exc).__name__,
        )
        return None
