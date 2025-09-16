# VoiceCast TTS Daemon

**VoiceCast** is a professional, production-ready Python daemon service that listens for POST requests with JSON payloads containing text, processes them through Deepgram TTS, and plays the audio on Google Nest devices. It uses FastAPI for a superior API development experience, automatic documentation, and built-in validation.

## Key Features

- **Daemon Mode**: Runs as a background service with proper process management.
- **FastAPI REST API**: Modern async API with automatic documentation and validation.
- **TTS Integration**: Deepgram API integration for high-quality text-to-speech conversion.
- **Google Cast**: Seamless integration with Google Nest/Chromecast devices.
- **Audio Management**: Intelligent file cleanup and retention policies.
- **Error Handling**: Comprehensive error handling with proper logging and recovery.
- **Configuration**: Environment-based configuration with validation.

## Technology Stack

- **Python 3.8+**
- **FastAPI**: For the REST API.
- **Uvicorn**: As the ASGI server.
- **Deepgram SDK**: For Text-to-Speech.
- **PyChromecast**: For Google Cast integration.
- **Pydantic**: For settings management and data validation.
- **Structlog**: For structured logging.
- **Pytest**: For testing.

## Installation

1.  **Prerequisites**: Make sure you have Python 3.8+ installed.

2.  **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd voicecast-daemon
    ```

3.  **Run the installation script**:

    ```bash
    ./install.sh
    ```

    This will:
    - Create a Python virtual environment in `.venv`.
    - Activate the virtual environment.
    - Install all the required dependencies from `requirements.txt`.
    - Create the `logs` and `audio` directories.
    - Create a `.env` file from the `.env.example` template.

4.  **Configure the application**:

    Edit the `.env` file to add your Deepgram API key, your VoiceCast API key, and specify your Google Cast device name.

    If you are running the daemon behind a reverse proxy or a tunnel service like Cloudflare Tunnel, you may need to set the `EXTERNAL_URL` variable in your `.env` file. This ensures that the audio URL provided to the Google Cast device is reachable from the public internet.

    **Example:**
    ```
    EXTERNAL_URL=https://your-public-domain.com
    ```

## API Security

The API is protected by API key authentication and rate limiting to ensure secure and fair usage.

### API Key Authentication

All endpoints (except for the health check endpoint) require API key authentication. You must provide a valid API key in the `X-API-Key` header of your requests.

**Example using cURL:**

```bash
curl -X POST "http://localhost:8080/api/v1/tts" 
     -H "Content-Type: application/json" 
     -H "X-API-Key: your_secret_api_key" 
     -d '{"text": "Hello world"}'
```

The API key can be configured in the `.env` file by setting the `API_KEY` variable.

### Cloudflare Access Authentication

In addition to API key authentication, the application can be configured to use Cloudflare Access service tokens for an additional layer of security. This is useful when you want to hide the service from the public internet and only allow access through Cloudflare Zero Trust.

To enable Cloudflare Access authentication, you need to set the following environment variables in your `.env` file:

- `CLOUDFLARE_ACCESS_CLIENT_ID`: Your Cloudflare Access client ID.
- `CLOUDFLARE_ACCESS_CLIENT_SECRET`: Your Cloudflare Access client secret.

When these variables are set, the application will require the `CF-Access-Client-Id` and `CF-Access-Client-Secret` headers to be present in all requests. If the headers are missing or invalid, the request will be rejected with a `403 Forbidden` error.

If these variables are not set, the Cloudflare Access authentication will be disabled.

### Rate Limiting

To prevent abuse and ensure fair usage, the API has a default rate limit of 100 requests per 60 seconds per IP address.
If you exceed this limit, you will receive a `429 Too Many Requests` response.

The rate limit can be configured in the `.env` file by setting the `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` variables.

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- **Swagger UI**: `http://<host>:<port>/docs`
- **ReDoc**: `http://<host>:<port>/redoc`

### Endpoints

- **`POST /api/v1/tts`**: The main endpoint for text-to-speech requests.
    - **Request Body**:
        ```json
        {
          "text": "Hello world",
          "voice": "aura-2-helena-en",
          "speed": 1.0
        }
        ```
    - **Response**:
        ```json
        {
          "audio_url": "/audio/file.wav",
          "duration": 2.5,
          "file_size": 12345
        }
        ```

- **`GET /api/v1/health`**: Health check endpoint.
- **`GET /api/v1/status`**: Detailed system status.

## Usage

### Command-line Arguments

The application provides the following command-line arguments when using the `start` command:

- `--host`: The host to bind the server to. Defaults to `0.0.0.0`.
- `--port`: The port to bind the server to. Defaults to `8080`.
- `--workers`: The number of worker processes. Defaults to `1`.
- `--reload`: Enable auto-reload when code changes are detected. This is a flag and is disabled by default.
- `--api-key`: The API key for authentication.
- `--deepgram-api-key`: The Deepgram API key.

To see a full list of available arguments and their descriptions, you can use the `--help` flag:

```bash
python main.py start --help
```

### Running in the Foreground

To run the application in the foreground for development or debugging purposes, use the following command:

```bash
python main.py start
```

### Running with Docker

A Dockerfile is provided for building and running the application in a container. The container image is automatically built and published to GitHub Container Registry on every release.

**Important:** To allow the application to discover Google Nest devices on your local network, you must run the container in host network mode.

To run the application using Docker, you can use the following command:

```bash
docker run -d \
  --name voicecast-daemon \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/audio:/app/audio \
  ghcr.io/alvinveroy/voicecast:latest
```




## Development

### Project Structure

The project follows a modular structure:

```
voicecast-daemon/
├── src/                     # Source code
│   ├── api/                 # FastAPI application
│   ├── config/              # Configuration
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   └── utils/               # Utility modules
├── tests/                   # Test suite
├── logs/                    # Log files
├── audio/                   # Generated audio files
└── ...
```

### Testing

To run the tests, use `pytest`:

```bash
source .venv/bin/activate
pytest
```

## Troubleshooting

### 403 Forbidden Error

If you are consistently receiving a `403 Forbidden` error when making requests to the API, even with what you believe is the correct API key, it is likely that the `.env` file is not being loaded correctly or is missing.

By default, the application uses the `.env.example` file, which contains placeholder values. The `install.sh` script is responsible for creating a `.env` file from this template, but if this step was skipped or failed, the application will fall back to the default settings, which include a placeholder API key.

To resolve this, you can manually create the `.env` file by copying the contents of `.env.example`:

```bash
cp .env.example .env
```

Once you have created the `.env` file, make sure to update the `API_KEY` value to your desired secret key.

```bash
API_KEY=your_secret_api_key
```
