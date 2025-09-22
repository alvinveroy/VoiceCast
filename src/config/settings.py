from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env' if "PYTEST_CURRENT_TEST" not in os.environ else None,
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Project root directory
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    EXTERNAL_URL: Optional[str] = None
    DEBUG: bool = False
    RELOAD: bool = False
    WORKERS: int = 1

    # FastAPI Configuration
    TITLE: str = "VoiceCast TTS Daemon API"
    DESCRIPTION: str = "Text-to-Speech service with Google Cast integration"
    VERSION: str = "1.0.0"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # Deepgram Configuration
    DEEPGRAM_API_KEY: str
    DEEPGRAM_MODEL: str = "aura-2-helena-en"
    DEEPGRAM_TIMEOUT: float = 30.0

    # Google Cast Configuration
    GOOGLE_CAST_DEVICE_NAME: Optional[str] = None
    CAST_DISCOVERY_TIMEOUT: float = 15.0
    CAST_DISCOVERY_TRIES: int = 3
    CAST_RETRY_WAIT: float = 5.0
    CAST_CONNECTION_TIMEOUT: float = 15.0
    CAST_PLAYBACK_TIMEOUT: float = 60.0

    # Audio Configuration
    AUDIO_OUTPUT_DIR: str = os.path.join(PROJECT_ROOT, "audio")
    AUDIO_RETENTION_DAYS: int = 7
    AUDIO_MAX_FILES: int = 50
    AUDIO_FORMAT: str = "wav"
    AUDIO_CACHE_ENABLED: bool = True
    AUDIO_CACHE_MAX_SIZE: int = 100

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = os.path.join(PROJECT_ROOT, "logs", "voicecast-daemon.log")
    LOG_MAX_SIZE: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    LOG_FORMAT: str = "json"

    # Daemon Configuration
    PID_FILE: str = os.path.join(PROJECT_ROOT, "voicecast-daemon.pid")

    # Security Configuration
    API_KEY: str
    CLOUDFLARE_ACCESS_CLIENT_ID: Optional[str] = None
    CLOUDFLARE_ACCESS_CLIENT_SECRET: Optional[str] = None
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    MAX_REQUEST_SIZE: int = 1048576
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # Watchdog Configuration
    DISCORD_WEBHOOK_URL: Optional[str] = None
    WATCHDOG_INTERVAL: int = 60
    CHROMECAST_DISCOVERY_INTERVAL: int = 300
    CHROMECAST_REFRESH_INTERVAL: int = 1800

@lru_cache()
def get_settings() -> Settings:
    return Settings()