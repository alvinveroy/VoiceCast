
import asyncio
import httpx
from src.config.settings import get_settings
from src.utils.logger import log
from src.services.device_registry import DeviceRegistry

settings = get_settings()

async def send_discord_notification(message: str):
    """Sends a notification to the Discord webhook."""
    if not settings.DISCORD_WEBHOOK_URL:
        return

    try:
        payload = {"content": message}
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        log.info("Sent Discord notification.", message=message)
    except httpx.RequestError as e:
        log.error("Failed to send Discord notification.", error=str(e))

async def check_internet_connection() -> bool:
    """Checks for internet connectivity by pinging Google's DNS."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://8.8.8.8")
        response.raise_for_status()
        return True
    except httpx.RequestError:
        return False

async def watchdog_loop(device_registry: DeviceRegistry):
    """The main loop for the watchdog service."""
    log.info("Starting watchdog service.")
    await send_discord_notification("Watchdog service started.")

    internet_down_since = None
    last_chromecast_check = 0
    last_chromecast_refresh = 0

    while True:
        # Check internet connection
        if await check_internet_connection():
            if internet_down_since:
                downtime = (asyncio.get_event_loop().time() - internet_down_since)
                await send_discord_notification(f"Internet connection is back online after {downtime:.2f} seconds.")
                internet_down_since = None
        else:
            if not internet_down_since:
                internet_down_since = asyncio.get_event_loop().time()
                await send_discord_notification("Internet connection is down.")

        now = asyncio.get_event_loop().time()

        # Check for Chromecast devices
        if now - last_chromecast_check > settings.CHROMECAST_DISCOVERY_INTERVAL:
            if not device_registry.get_all_devices():
                await send_discord_notification("No Chromecast devices detected. Starting a new discovery process.")
                await device_registry.discover_devices()
            last_chromecast_check = now

        # Refresh Chromecast devices
        if now - last_chromecast_refresh > settings.CHROMECAST_REFRESH_INTERVAL:
            await send_discord_notification("Refreshing Chromecast devices.")
            await device_registry.refresh_devices()
            last_chromecast_refresh = now

        await asyncio.sleep(settings.WATCHDOG_INTERVAL)
