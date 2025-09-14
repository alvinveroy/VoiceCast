import pytest
import subprocess
import sys
import time
import requests
import os
import signal
from src.config.settings import get_settings

# Helper function to wait for the server to start
def wait_for_server(host="localhost", port=8080, timeout=120):
    start_time = time.time()
    while True:
        try:
            response = requests.get(f"http://{host}:{port}/api/v1/health")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        if time.time() - start_time > timeout:
            raise RuntimeError("Server did not start in time")
        time.sleep(0.5)

import socket

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    addr, port = s.getsockname()
    s.close()
    return port

@pytest.mark.e2e
def test_e2e_media_interruption(mocker):
    mocker.patch("src.services.tts_service.TTSService.generate_audio", return_value="/tmp/test.wav")
    project_root = get_settings().PROJECT_ROOT
    port = get_free_port()
    # Start the server directly in the background
    env = os.environ.copy()
    env["API_KEY"] = "test_api_key"
    env["DEEPGRAM_API_KEY"] = "test_deepgram_key"
    env["PORT"] = str(port)
    process = subprocess.Popen(
        [sys.executable, "main.py", "start"],
        cwd=project_root,
        stdout=subprocess.PIPE, # Capture stdout
        stderr=subprocess.PIPE, # Capture stderr
        text=True, # Decode as text
        env=env
    )
    wait_for_server(port=port)

    try:
        # Cast a long-playing video
        long_video_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        headers = {"X-API-Key": "test_api_key"}
        requests.post(f"http://localhost:{port}/api/v1/tts", json={"text": f"<speak><audio src=\"{long_video_url}\"/></speak>"}, headers=headers)
        time.sleep(5) # Let the video play for a bit

        # Send a TTS request to interrupt
        tts_response = requests.post(f"http://localhost:{port}/api/v1/tts", json={"text": "This should interrupt the video."}, headers=headers)
        print(tts_response.json())
    finally:
        # Stop the server gracefully
        process.send_signal(signal.SIGINT)
        try:
            stdout, stderr = process.communicate(timeout=15) # Wait for graceful shutdown
            print("Server stdout:", stdout)
            print("Server stderr:", stderr)
        except subprocess.TimeoutExpired:
            print("Server did not shut down gracefully, killing it.")
            process.kill()
            stdout, stderr = process.communicate()
            print("Server stdout after kill:", stdout)
            print("Server stderr after kill:", stderr)

    assert tts_response.status_code == 200
    response_json = tts_response.json()
    assert response_json["message"] == "TTS request added to queue"
    assert "task_id" in response_json
    assert isinstance(response_json["task_id"], str)