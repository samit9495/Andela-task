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

    # --- Security ---
    request_body_max_bytes: int = Field(default=1_048_576, alias="WATCHDOG_REQUEST_BODY_MAX_BYTES")
    cors_allow_origins: str = Field(
        default="http://localhost:5173", alias="WATCHDOG_CORS_ALLOW_ORIGINS"
    )

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    use_mock_ai: bool = Field(default=False, alias="USE_MOCK_AI")
    model_name: str = Field(default="gemini-1.5-flash", alias="MODEL_NAME")

    # --- Detection (see MASTER_PLAN section 26.2) ---
    detection_bucket_seconds: int = Field(default=60, alias="DETECTION_BUCKET_SECONDS")
    z_score_threshold: float = Field(default=3.0, alias="DETECTION_Z_SCORE_THRESHOLD")
    min_baseline_samples: int = Field(default=10, alias="DETECTION_MIN_BASELINE_SAMPLES")
    ewma_alpha: float = Field(default=0.3, alias="DETECTION_EWMA_ALPHA")
    ewma_drift_threshold: float = Field(default=3.0, alias="DETECTION_EWMA_DRIFT_THRESHOLD")
    signature_burst_multiplier: float = Field(
        default=5.0, alias="DETECTION_SIGNATURE_BURST_MULTIPLIER"
    )
    signature_burst_floor: int = Field(default=10, alias="DETECTION_SIGNATURE_MIN_ABSOLUTE")

    # --- Correlation (see MASTER_PLAN section 26.1) ---
    correlation_window_seconds: int = Field(default=300, alias="CORRELATION_WINDOW_SECONDS")

    # --- Triage / RAG (see MASTER_PLAN sections 12-13) ---
    runbook_dir: str = Field(default="data/runbooks", alias="RUNBOOK_DIR")
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    rag_min_similarity: float = Field(default=0.05, alias="RAG_MIN_SIMILARITY")
    llm_prompt_log_path: str = Field(default="docs/llm_prompts.md", alias="LLM_PROMPT_LOG_PATH")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")

    # --- Alerts (see MASTER_PLAN Component 11) ---
    alert_rate_limit_seconds: int = Field(default=300, alias="ALERT_RATE_LIMIT_SECONDS")

    # --- Risk score (MASTER_PLAN section 26.3) ---
    risk_error_rate_window_seconds: int = Field(
        default=900, alias="WATCHDOG_RISK_ERROR_RATE_WINDOW_SECONDS"
    )

    # --- Topology (see MASTER_PLAN Component 6) ---
    topology_path: str = Field(default="data/topology.json", alias="TOPOLOGY_PATH")

    @property
    def cors_origins(self) -> list[str]:
        """Parse the comma-separated CORS allowlist into a list of origins."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

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
