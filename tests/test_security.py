import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from src.api.security import verify_cloudflare_access
from src.config.settings import Settings, get_settings

@pytest.fixture
def settings_cf_enabled():
    return Settings(
        API_KEY="test_api_key",
        DEEPGRAM_API_KEY="test_deepgram_key",
        CLOUDFLARE_ACCESS_CLIENT_ID="test_client_id",
        CLOUDFLARE_ACCESS_CLIENT_SECRET="test_client_secret",
    )

@pytest.fixture
def settings_cf_disabled():
    return Settings(API_KEY="test_api_key", DEEPGRAM_API_KEY="test_deepgram_key")

def create_test_app():
    app = FastAPI(dependencies=[Depends(verify_cloudflare_access)])

    @app.get("/")
    def read_root():
        return {"Hello": "World"}

    return app


def test_cloudflare_access_success(settings_cf_enabled):
    app = create_test_app()
    app.dependency_overrides[get_settings] = lambda: settings_cf_enabled
    client = TestClient(app)
    headers = {
        "CF-Access-Client-Id": "test_client_id",
        "CF-Access-Client-Secret": "test_client_secret",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200

def test_cloudflare_access_failure_missing_headers(settings_cf_enabled):
    app = create_test_app()
    app.dependency_overrides[get_settings] = lambda: settings_cf_enabled
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 403

def test_cloudflare_access_failure_invalid_credentials(settings_cf_enabled):
    app = create_test_app()
    app.dependency_overrides[get_settings] = lambda: settings_cf_enabled
    client = TestClient(app)
    headers = {
        "CF-Access-Client-Id": "wrong_client_id",
        "CF-Access-Client-Secret": "wrong_client_secret",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 403

def test_cloudflare_access_disabled(settings_cf_disabled):
    app = create_test_app()
    app.dependency_overrides[get_settings] = lambda: settings_cf_disabled
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
