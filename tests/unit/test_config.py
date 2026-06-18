"""Unit tests for configuration loading."""

from backend.app.core.config import Settings


class TestSettings:
    def test_defaults_when_env_absent(self):
        settings = Settings(_env_file=None)

        assert settings.app_name
        assert settings.app_version == "0.1.0"
        assert settings.log_level == "INFO"
        assert settings.database_url.startswith("sqlite")

    def test_env_override_is_applied(self, monkeypatch):
        monkeypatch.setenv("WATCHDOG_LOG_LEVEL", "DEBUG")

        settings = Settings(_env_file=None)

        assert settings.log_level == "DEBUG"

    def test_ai_mode_is_mock_when_no_api_key(self):
        settings = Settings(_env_file=None, gemini_api_key="", use_mock_ai=False)

        assert settings.ai_mode == "mock"

    def test_ai_mode_is_mock_when_use_mock_ai_true(self):
        settings = Settings(_env_file=None, gemini_api_key="real-key", use_mock_ai=True)

        assert settings.ai_mode == "mock"

    def test_ai_mode_is_mock_for_placeholder_key(self):
        settings = Settings(_env_file=None, gemini_api_key="replace-me", use_mock_ai=False)

        assert settings.ai_mode == "mock"

    def test_ai_mode_is_gemini_when_real_key_and_not_mock(self):
        settings = Settings(_env_file=None, gemini_api_key="AItestkey123", use_mock_ai=False)

        assert settings.ai_mode == "gemini"
