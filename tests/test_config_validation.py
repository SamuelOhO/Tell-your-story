import pytest

from backend import config as config_module


def _clear_cache() -> None:
    config_module.get_settings.cache_clear()


def test_invalid_max_history_turns_raises_value_error(monkeypatch):
    monkeypatch.setenv("MAX_HISTORY_TURNS", "0")
    _clear_cache()
    with pytest.raises(ValueError, match="MAX_HISTORY_TURNS must be between 1 and 100"):
        config_module.get_settings()


def test_invalid_allowed_origin_raises_value_error(monkeypatch):
    monkeypatch.setenv("MAX_HISTORY_TURNS", "12")
    monkeypatch.setenv("ALLOWED_ORIGINS", "localhost:5173")
    _clear_cache()
    with pytest.raises(ValueError, match="Invalid ALLOWED_ORIGINS entry"):
        config_module.get_settings()


def test_invalid_log_level_raises_value_error(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.setenv("LOG_LEVEL", "TRACE")
    _clear_cache()
    with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
        config_module.get_settings()


def test_valid_settings_load(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.setenv("MAX_HISTORY_TURNS", "12")
    monkeypatch.setenv("SUMMARY_UPDATE_EVERY", "6")
    monkeypatch.setenv("DB_PATH", "backend/data/test.db")
    _clear_cache()
    settings = config_module.get_settings()
    assert settings.app_env == "dev"
    assert settings.max_history_turns == 12
    assert settings.summary_update_every == 6
