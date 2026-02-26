import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("UPSTAGE_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
client = None
if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)

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
    except Exception as e:
        print(f"Error in TTS: {type(e).__name__}")
        return None
