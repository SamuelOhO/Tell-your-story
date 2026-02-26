from openai import OpenAI
from ..config import get_settings

settings = get_settings()
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
    except Exception as e:
        print(f"Error in transcription: {type(e).__name__}")
        return ""
