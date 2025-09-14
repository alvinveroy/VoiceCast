import logging
import logging.config
import structlog
from src.config.settings import Settings

def setup_logging(settings: Settings):
    """Set up logging configuration."""
    log_level = settings.LOG_LEVEL.upper()

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        processors=shared_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "()": "structlog.stdlib.ProcessorFormatter",
                    "processor": structlog.dev.ConsoleRenderer(),
                    "foreign_pre_chain": shared_processors,
                },
                "json": {
                    "()": "structlog.stdlib.ProcessorFormatter",
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "console": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                },
                "file": {
                    "level": log_level,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": settings.LOG_FILE,
                    "maxBytes": settings.LOG_MAX_SIZE,
                    "backupCount": settings.LOG_BACKUP_COUNT,
                    "formatter": "json",
                },
            },
            "loggers": {
                "uvicorn.error": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "": {
                    "handlers": ["console", "file"],
                    "level": log_level,
                    "propagate": True,
                },
            },
        }
    )

log = structlog.get_logger()