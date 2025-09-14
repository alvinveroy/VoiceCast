import pychromecast
import time
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# Get the device name from the environment variable
CAST_DEVICE_NAME = os.getenv("GOOGLE_CAST_DEVICE_NAME")

if not CAST_DEVICE_NAME:
    print("Error: GOOGLE_CAST_DEVICE_NAME environment variable not set.")
    exit(1)

if len(sys.argv) < 2:
    print("Error: Please provide the path to the audio file.")
    exit(1)

audio_file_path = sys.argv[1]
if not os.path.exists(audio_file_path):
    print(f"Error: File not found at {audio_file_path}")
    exit(1)

print(f"Searching for device: {CAST_DEVICE_NAME}")

chromecasts, browser = pychromecast.get_listed_chromecasts()

if not chromecasts:
    print("No devices found.")
    exit()

cast = next((cc for cc in chromecasts if cc.name == CAST_DEVICE_NAME), None)

if cast:
    cast.wait()
    print(f"Found and connected to {cast.name}")
    mc = cast.media_controller
    
    # Play the local audio file
    mc.play_media(f"http://127.0.0.1:8086/audio/{os.path.basename(audio_file_path)}", "audio/wav")
    
    mc.block_until_active()
    print("Playing media...")
    
    while mc.status.player_is_playing:
        time.sleep(1)
        
    print("Playback finished.")
else:
    print(f"Device '{CAST_DEVICE_NAME}' not found.")

browser.stop_discovery()
