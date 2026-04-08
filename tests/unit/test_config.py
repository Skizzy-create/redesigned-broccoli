from app.config import get_settings


def test_settings_defaults():
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.app_name == "Smart Document Q&A API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.api_key == "dev-api-key"


def test_settings_override_from_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_NAME", "Overridden Name")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("API_KEY", "custom-key")

    settings = get_settings()

    assert settings.app_name == "Overridden Name"
    assert settings.app_version == "1.2.3"
    assert settings.api_key == "custom-key"


def test_settings_instance_is_cached():
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
