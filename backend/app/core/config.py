"""Application configuration loaded from environment variables.

All settings are read from the environment (optionally a local ``.env`` file)
via ``pydantic-settings``. Secrets never live in source; see ``.env.example``
for the full list of supported variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_KEYS = {"", "replace-me", "changeme", "your-api-key"}


class Settings(BaseSettings):
    """Typed application settings with documented defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="Agentic Observability Platform", alias="WATCHDOG_APP_NAME")
    app_version: str = Field(default="0.1.0", alias="WATCHDOG_APP_VERSION")

    log_level: str = Field(default="INFO", alias="WATCHDOG_LOG_LEVEL")

    database_url: str = Field(default="sqlite:///./var/watchdog.db", alias="WATCHDOG_DATABASE_URL")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    use_mock_ai: bool = Field(default=False, alias="USE_MOCK_AI")
    model_name: str = Field(default="gemini-1.5-flash", alias="MODEL_NAME")

    @property
    def ai_mode(self) -> str:
        """Return ``"gemini"`` only when a real key is set and mock is disabled."""
        if self.use_mock_ai:
            return "mock"
        if self.gemini_api_key.strip().lower() in _PLACEHOLDER_KEYS:
            return "mock"
        return "gemini"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance for dependency injection."""
    return Settings()
