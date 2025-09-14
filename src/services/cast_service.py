import pychromecast
from src.config.settings import Settings
from src.utils.logger import log
import asyncio
from src.utils.network_utils import get_local_ip
from src.utils.singleton import get_cast_browser, get_zeroconf_instance

class CastService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.device_name = self.settings.GOOGLE_CAST_DEVICE_NAME
        self.chromecast = None
        self._host_ip = None

    @property
    def host_ip(self):
        if self._host_ip is None:
            if self.settings.HOST == "0.0.0.0":
                self._host_ip = get_local_ip()
            else:
                self._host_ip = self.settings.HOST
        return self._host_ip

    async def discover_and_connect(self, device_name: str = None):
        """Discover and connect to a Google Cast device asynchronously."""
        log.info("Discovering Google Cast devices...")

        browser, listener = get_cast_browser()
        zconf = get_zeroconf_instance()

        try:
            # Start discovery if not already running
            if not browser.is_discovering:
                await asyncio.to_thread(browser.start_discovery)

            await asyncio.sleep(self.settings.CAST_DISCOVERY_TIMEOUT)

            target_device_name = device_name or self.device_name
            cast_info = next((c for c in listener.devices if c.friendly_name == target_device_name), None)

            if not cast_info:
                log.warning(f"Device '{target_device_name}' not found.")
                return False

            self.chromecast = await asyncio.to_thread(
                pychromecast.get_chromecast_from_cast_info, cast_info, zconf
            )
            await asyncio.to_thread(self.chromecast.wait)
            log.info(f"Connected to {self.chromecast.name}")
            return True

        except Exception as e:
            log.error(f"An error occurred during device discovery: {e}")
            return False

    async def play_audio(self, audio_url: str, device_name: str = None):
        """Play audio on the connected Google Cast device."""
        log.info(f"Attempting to play audio from URL: {audio_url}")
        if not self.chromecast or not self.chromecast.is_idle or (device_name and self.chromecast.name != device_name):
            if not await self.discover_and_connect(device_name):
                log.error("Could not connect to device for playback.")
                return
        
        await asyncio.sleep(1) # Add a small delay

        mc = self.chromecast.media_controller

        # Stop any currently playing media
        if mc.status.player_is_playing or mc.status.player_is_paused:
            log.info("Stopping current media playback.")
            mc.stop()
            await asyncio.sleep(1) # Give it a moment to stop

        log.info(f"Playing audio from file: {audio_url}")
        mc.play_media(audio_url, "audio/wav")
        mc.block_until_active()
        log.info("Audio playback started.")

    
