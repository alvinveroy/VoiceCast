import logging
import logging.config
import structlog
from src.config.settings import Settings
from rich.logging import RichHandler

def setup_logging(settings: Settings):
    """Set up logging configuration."""
    log_level = settings.LOG_LEVEL.upper()

    if settings.LOG_FORMAT == "console":
        # Simple RichHandler configuration for console output
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
        )
    else:
        # Structlog configuration for JSON output
        shared_processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "json": {
                        "()": structlog.stdlib.ProcessorFormatter,
                        "processor": structlog.processors.JSONRenderer(),
                        "foreign_pre_chain": shared_processors,
                    },
                },
                "handlers": {
                    "default": {
                        "level": log_level,
                        "class": "logging.StreamHandler",
                        "formatter": "json",
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
                        "handlers": ["file"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "uvicorn.access": {
                        "handlers": ["file"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "": {
                        "handlers": ["default", "file"],
                        "level": log_level,
                        "propagate": True,
                    },
                },
            }
        )

        structlog.configure(
            processors=shared_processors + [structlog.processors.JSONRenderer()],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=False,
        )

log = structlog.get_logger()