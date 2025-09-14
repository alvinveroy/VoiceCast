import click
from src.config.settings import get_settings
from src.utils.logger import setup_logging, log
import uvicorn
import pychromecast

# Monkey patch the CastBrowser to add the is_discovering attribute
pychromecast.CastBrowser.is_discovering = False
original_start_discovery = pychromecast.CastBrowser.start_discovery
original_stop_discovery = pychromecast.CastBrowser.stop_discovery

def start_discovery_patched(self):
    self.is_discovering = True
    return original_start_discovery(self)

def stop_discovery_patched(self):
    self.is_discovering = False
    return original_stop_discovery(self)

pychromecast.CastBrowser.start_discovery = start_discovery_patched
pychromecast.CastBrowser.stop_discovery = stop_discovery_patched

# Get settings at the top level
settings = get_settings()

def main_app(host, port, workers, api_key, deepgram_api_key):
    """Start the VoiceCast server."""
    from src.api.app import create_app # Moved inside function

    if api_key:
        settings.API_KEY = api_key
    if deepgram_api_key:
        settings.DEEPGRAM_API_KEY = deepgram_api_key

    app = create_app(settings)
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
    )

@click.group()
def cli():
    pass

@cli.command()
@click.option("--host", default=settings.HOST, help="Host to bind to.")
@click.option("--port", default=settings.PORT, help="Port to bind to.")
@click.option("--workers", default=settings.WORKERS, help="Number of worker processes.")
@click.option("--reload", is_flag=True, default=settings.RELOAD, help="Enable auto-reload.")
@click.option("--api-key", help="API key for authentication.")
@click.option("--deepgram-api-key", help="Deepgram API key.")
def start(host, port, workers, reload, api_key, deepgram_api_key):
    """Start the VoiceCast server."""
    setup_logging(settings)
    log.info("Starting VoiceCast server in foreground.")
    main_app(host, port, workers, api_key, deepgram_api_key)





if __name__ == "__main__":
    cli()





if __name__ == "__main__":
    cli()





if __name__ == "__main__":
    cli()





if __name__ == "__main__":
    cli()