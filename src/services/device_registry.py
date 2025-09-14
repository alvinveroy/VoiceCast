import asyncio
from typing import Dict, Optional
from src.config.settings import Settings
from src.utils.logger import log
from src.utils.singleton import get_cast_browser
import threading

class DeviceRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._devices: Dict[str, dict] = {}
        self._generation = 0
        self._discovery_lock = threading.Lock()

    async def discover_devices(self):
        if not self._discovery_lock.acquire(blocking=False):
            log.info("Discovery is already in progress.")
            return

        log.info("Starting device discovery...")
        
        try:
            browser, listener = get_cast_browser()
            
            # Start discovery if not already running
            if not browser.is_discovering:
                await asyncio.to_thread(browser.start_discovery)

            await asyncio.sleep(self.settings.CAST_DISCOVERY_TIMEOUT)

            new_devices = {}
            for cast_info in listener.devices:
                device_info = {
                    "uuid": str(cast_info.uuid),
                    "friendly_name": cast_info.friendly_name,
                    "host": cast_info.host,
                    "port": cast_info.port,
                    "cast_type": cast_info.cast_type,
                    "last_seen": asyncio.get_event_loop().time(),
                }
                new_devices[cast_info.friendly_name.lower()] = device_info

            self._devices = new_devices
            self._generation += 1
            log.info(f"Discovered {len(self._devices)} devices in generation {self._generation}.")
        finally:
            self._discovery_lock.release()

    def get_devices(self) -> dict:
        return {"generation": self._generation, "devices": list(self._devices.values())}

    def get_device_by_name(self, name: str) -> Optional[dict]:
        return self._devices.get(name.lower())

    async def refresh_devices(self):
        await self.discover_devices()

    