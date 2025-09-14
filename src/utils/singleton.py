import zeroconf
import pychromecast
from src.utils.discovery import CastListener

_zeroconf_instance = None
_cast_browser = None
_cast_listener = None

def get_zeroconf_instance():
    """Returns a singleton Zeroconf instance."""
    global _zeroconf_instance
    if _zeroconf_instance is None:
        _zeroconf_instance = zeroconf.Zeroconf()
    return _zeroconf_instance

def create_cast_browser():
    """Creates a new CastBrowser instance."""
    zconf = get_zeroconf_instance()
    listener = CastListener()
    browser = pychromecast.CastBrowser(listener, zconf)
    listener.browser = browser
    return browser, listener

def get_cast_browser():
    """Returns a singleton CastBrowser instance."""
    global _cast_browser, _cast_listener
    if _cast_browser is None:
        _cast_browser, _cast_listener = create_cast_browser()
    return _cast_browser, _cast_listener


