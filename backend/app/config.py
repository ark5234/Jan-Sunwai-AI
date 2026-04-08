import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _parse_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_access_token_expiry_minutes() -> int:
    explicit = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    if explicit:
        return int(explicit)
    app_env = os.getenv("APP_ENV", "development").lower()
    # NDMC-facing default: shorter TTL in production.
    return 480 if app_env == "production" else 1440


def _default_rate_limit_enabled() -> bool:
    explicit = os.getenv("RATE_LIMIT_ENABLED")
    if explicit is not None:
        return explicit.strip().lower() in ("true", "1", "yes", "on")
    # Local/dev should work even without optional dependencies.
    return os.getenv("APP_ENV", "development").lower() == "production"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    mongodb_url: str = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    db_name: str = os.getenv("DB_NAME", "jan_sunwai_db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = _default_access_token_expiry_minutes()
    enable_rate_limiting: bool = _default_rate_limit_enabled()
    allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    vision_model: str = os.getenv("VISION_MODEL", "qwen2.5vl:3b")
    mid_vision_model: str = os.getenv("MID_VISION_MODEL", "granite3.2-vision:2b")
    fallback_vision_model: str = os.getenv("FALLBACK_VISION_MODEL", "granite3.2-vision:2b")
    reasoning_model: str = os.getenv("REASONING_MODEL", "llama3.2:1b")
    translation_model: str = os.getenv("TRANSLATION_MODEL", "").strip()
    enable_ollama_translation_fallback: bool = os.getenv("ENABLE_OLLAMA_TRANSLATION_FALLBACK", "false").lower() in ("true", "1", "yes")
    vision_timeout_seconds: float = float(os.getenv("VISION_TIMEOUT_SECONDS", "240"))
    llm_inline_timeout_seconds: float = float(os.getenv("LLM_INLINE_TIMEOUT_SECONDS", "15"))
    llm_queue_workers: int = int(os.getenv("LLM_QUEUE_WORKERS", "2"))
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "25"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    rule_engine_only: bool = os.getenv("RULE_ENGINE_ONLY", "false").lower() in ("true", "1", "yes")
    ambiguity_threshold: float = float(os.getenv("AMBIGUITY_THRESHOLD", "2.0"))
    unload_after_reasoning: bool = os.getenv("UNLOAD_AFTER_REASONING", "true").lower() in ("true", "1", "yes")
    model_unload_timeout_seconds: float = float(os.getenv("MODEL_UNLOAD_TIMEOUT_SECONDS", "30"))
    model_unload_poll_interval_seconds: float = float(os.getenv("MODEL_UNLOAD_POLL_INTERVAL_SECONDS", "0.1"))
    keep_reasoning_model_warm: bool = os.getenv("KEEP_REASONING_MODEL_WARM", "false").lower() in ("true", "1", "yes")
    complaint_output_mode: str = os.getenv("COMPLAINT_OUTPUT_MODE", "email").strip().lower()

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@jan-sunwai.local")

    @property
    def allowed_origins(self) -> list[str]:
        return _parse_origins(self.allowed_origins_raw)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
