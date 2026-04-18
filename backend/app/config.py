import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


def _parse_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """
    Typed application settings loaded from environment variables / .env file.
    P4-B: Migrated from dataclass + os.getenv() to pydantic-settings for
    proper validation, type coercion, and test-override support.
    """

    # App
    app_env: str = Field(default="development", alias="APP_ENV")

    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    db_name: str = Field(default="jan_sunwai_db", alias="DB_NAME")

    # JWT
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    return_access_token_in_response: bool = Field(
        default=False,
        alias="RETURN_ACCESS_TOKEN_IN_RESPONSE",
    )

    # CORS
    allowed_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(default=False, alias="RATE_LIMIT_ENABLED")

    # LLM / Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    vision_model: str = Field(default="qwen2.5vl:3b", alias="VISION_MODEL")
    mid_vision_model: str = Field(default="granite3.2-vision:2b", alias="MID_VISION_MODEL")
    fallback_vision_model: str = Field(default="granite3.2-vision:2b", alias="FALLBACK_VISION_MODEL")
    reasoning_model: str = Field(default="llama3.2:1b", alias="REASONING_MODEL")
    translation_model: str = Field(default="", alias="TRANSLATION_MODEL")
    enable_ollama_translation_fallback: bool = Field(
        default=False, alias="ENABLE_OLLAMA_TRANSLATION_FALLBACK"
    )
    vision_timeout_seconds: float = Field(default=240.0, alias="VISION_TIMEOUT_SECONDS")
    llm_inline_timeout_seconds: float = Field(default=8.0, alias="LLM_INLINE_TIMEOUT_SECONDS")
    llm_queue_workers: int = Field(default=2, alias="LLM_QUEUE_WORKERS")

    # Classifier / Rule engine
    rule_engine_only: bool = Field(default=False, alias="RULE_ENGINE_ONLY")
    ambiguity_threshold: float = Field(default=2.0, alias="AMBIGUITY_THRESHOLD")
    unload_after_reasoning: bool = Field(default=True, alias="UNLOAD_AFTER_REASONING")
    model_unload_timeout_seconds: float = Field(default=30.0, alias="MODEL_UNLOAD_TIMEOUT_SECONDS")
    model_unload_poll_interval_seconds: float = Field(
        default=0.1, alias="MODEL_UNLOAD_POLL_INTERVAL_SECONDS"
    )
    keep_reasoning_model_warm: bool = Field(default=False, alias="KEEP_REASONING_MODEL_WARM")
    complaint_output_mode: str = Field(default="email", alias="COMPLAINT_OUTPUT_MODE")

    # Email / SMTP — P1-G: adds username/password for STARTTLS auth
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_from: str = Field(default="noreply@jan-sunwai.local", alias="SMTP_FROM")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")

    # Pagination
    default_page_size: int = Field(default=25, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")

    # ── derived ──────────────────────────────────────────────────────────────

    @property
    def allowed_origins(self) -> list[str]:
        return _parse_origins(self.allowed_origins_raw)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def enable_rate_limiting(self) -> bool:
        """Alias kept for backwards compat with rate_limiter.py."""
        return self.rate_limit_enabled

    # ── pydantic-settings config ──────────────────────────────────────────────

    model_config = {  # type: ignore[misc]
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
        "protected_namespaces": ("settings_",),
    }

    @field_validator("mongodb_url", mode="before")
    @classmethod
    def _coerce_mongo_url(cls, v: str | None) -> str:
        """Accept MONGODB_URL or MONGO_URL (legacy alias)."""
        if not v:
            mongo_url = os.getenv("MONGO_URL", "")
            if mongo_url:
                return mongo_url
            return "mongodb://localhost:27017"
        return v

    @field_validator("access_token_expire_minutes", mode="before")
    @classmethod
    def _default_token_expiry(cls, v: int | str | None) -> int:
        if v is None or v == "":
            app_env = os.getenv("APP_ENV", "development").lower()
            return 480 if app_env == "production" else 1440
        return int(v)


settings = Settings()
