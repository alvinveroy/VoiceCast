import os
import httpx
import asyncio
from deepgram import DeepgramClient
from src.config.settings import Settings
from src.models.requests import TTSRequest
import structlog
import time

class TTSService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.deepgram = DeepgramClient(self.settings.DEEPGRAM_API_KEY)
        self.log = structlog.get_logger(__name__)

    async def generate_audio(self, tts_request: TTSRequest) -> str:
        self.log.info("Requesting TTS from Deepgram", text=tts_request.text, voice=tts_request.voice)
        try:
            # Ensure the audio directory exists
            os.makedirs(self.settings.AUDIO_OUTPUT_DIR, exist_ok=True)

            file_path = os.path.join(self.settings.AUDIO_OUTPUT_DIR, f"{int(time.time())}.wav")

            await asyncio.to_thread(
                self.deepgram.speak.rest.v("1").save,
                file_path,
                {"text": tts_request.text},
                {"model": tts_request.voice}
            )
            
            self.log.info("Successfully generated audio file", path=file_path)
            return file_path
        except httpx.HTTPStatusError as e:
            self.log.error("Deepgram API error", status_code=e.response.status_code, response=e.response.text)
            raise
        except Exception as e:
            self.log.error("Error generating audio", error=str(e))
            raise
