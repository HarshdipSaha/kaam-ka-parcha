import pytest
from fastapi.testclient import TestClient
from parcha.app import create_app
from parcha.config import Settings


def test_offline_health_does_not_need_credentials(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_settings_keep_rest_as_safe_default():
    settings = Settings.from_mapping({"API_KEY": "example"})
    assert settings.gnani_base_url == "https://api.vachana.ai"
    assert settings.reply_transport == "rest"


def test_settings_require_gnani_validation():
    settings = Settings(api_key="")
    with pytest.raises(ValueError, match="API_KEY is required"):
        settings.require_gnani()

    settings_placeholder = Settings(api_key="replace_me")
    with pytest.raises(ValueError, match="API_KEY is required"):
        settings_placeholder.require_gnani()

    valid_settings = Settings(api_key="valid-key")
    valid_settings.require_gnani()


def test_settings_require_extractor_validation():
    settings = Settings(extractor_base_url="", extractor_model="llama-3.3-70b-versatile")
    with pytest.raises(ValueError, match="An extractor endpoint and model are required"):
        settings.require_extractor()

    settings_no_model = Settings(extractor_base_url="https://api.groq.com/openai/v1", extractor_model="")
    with pytest.raises(ValueError, match="An extractor endpoint and model are required"):
        settings_no_model.require_extractor()

    valid = Settings(extractor_base_url="https://api.groq.com/openai/v1", extractor_model="llama-3.3-70b-versatile")
    valid.require_extractor()


def test_settings_fallback_to_groq_api_key():
    settings = Settings.from_mapping({"GROQ_API_KEY": "groq-secret"})
    assert settings.extractor_api_key == "groq-secret"
    assert settings.extractor_base_url == "https://api.groq.com/openai/v1"
    assert settings.extractor_model == "llama-3.3-70b-versatile"


def test_settings_load_returns_settings_instance():
    settings = Settings.load()
    assert isinstance(settings, Settings)

