import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("UPSTAGE_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)

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
