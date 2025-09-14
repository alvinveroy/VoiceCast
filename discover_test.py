import pychromecast

chromecasts, browser = pychromecast.get_listed_chromecasts()
print(f"Found {len(chromecasts)} devices")
for cast in chromecasts:
    print(cast)

browser.stop_discovery()
