import asyncio
from collections import deque
from src.services.tts_service import TTSService
from src.services.cast_service import CastService
from src.config.settings import Settings
import structlog # Import structlog
import os # Import os
import uuid

class QueueService:
    def __init__(self, tts_service: TTSService, cast_service: CastService, settings: Settings):
        self.queue = deque()
        self.tts_service = tts_service
        self.cast_service = cast_service
        self.settings = settings
        self.processing = False
        self.log = structlog.get_logger(__name__) # Get logger after setup_logging is called

    def add_to_queue(self, task: dict) -> str:
        task_id = str(uuid.uuid4())
        self.log.info("Adding task to queue", task_id=task_id)
        self.queue.append((task_id, task))
        if not self.processing:
            asyncio.create_task(self._process_queue())
        return task_id

    async def _process_queue(self):
        self.processing = True
        while self.queue:
            task_id, task = self.queue.popleft()
            tts_request = task["tts_request"]
            port = task["port"]
            device_name = tts_request.device_name # Extract device_name from tts_request

            self.log.info("Processing task from queue", task_id=task_id, text=tts_request.text, device_name=device_name)
            try:
                audio_file_full_path = await self.tts_service.generate_audio(tts_request)
                audio_filename = os.path.basename(audio_file_full_path)
                audio_url = f"http://{self.cast_service.host_ip}:{port}/audio/{audio_filename}"

                await self.cast_service.play_audio(audio_url, device_name)
                self.log.info("Finished processing task from queue", task_id=task_id, text=tts_request.text, device_name=device_name)
            except Exception as e:
                self.log.error("Error processing task from queue", task_id=task_id, text=tts_request.text, device_name=device_name, error=str(e))
        self.processing = False
