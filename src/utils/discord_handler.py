import httpx
import logging

class DiscordHandler(logging.Handler):
    """A logging handler that sends logs to a Discord webhook."""

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url

    def emit(self, record: logging.LogRecord):
        """Sends a log record to the Discord webhook."""
        if not self.webhook_url:
            return

        log_entry = self.format(record)
        payload = {"content": f"```\n{log_entry}```"}

        try:
            with httpx.Client() as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
        except httpx.RequestError as e:
            # We can't log this error to Discord, so we just print it
            print(f"Failed to send log to Discord: {e}")

