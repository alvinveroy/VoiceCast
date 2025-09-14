from pychromecast.discovery import SimpleCastListener

class CastListener(SimpleCastListener):
    def __init__(self):
        super().__init__(add_callback=self.add_cast, remove_callback=self.remove_cast, update_callback=self.update_cast)
        self.devices = []

    def add_cast(self, uuid, service):  # noqa
        self.devices.append(self.browser.devices[uuid])

    def remove_cast(self, uuid, service, cast_info):  # noqa
        # This can be implemented if needed
        pass

    def update_cast(self, uuid, service):  # noqa
        # This can be implemented if needed
        pass
