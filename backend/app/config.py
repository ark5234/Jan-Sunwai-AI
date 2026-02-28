import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _parse_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    mongodb_url: str = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    db_name: str = os.getenv("DB_NAME", "jan_sunwai_db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    vision_model: str = os.getenv("VISION_MODEL", "qwen2.5vl:3b")
    reasoning_model: str = os.getenv("REASONING_MODEL", "llama3.2:1b")
    llm_inline_timeout_seconds: float = float(os.getenv("LLM_INLINE_TIMEOUT_SECONDS", "8"))
    llm_queue_workers: int = int(os.getenv("LLM_QUEUE_WORKERS", "2"))
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "25"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    # ── VRAM-aware settings for hybrid classifier ──
    # rule_engine_only: if True, skip reasoning model entirely (saves ~1.2 GB VRAM)
    rule_engine_only: bool = os.getenv("RULE_ENGINE_ONLY", "false").lower() in ("true", "1", "yes")
    # ambiguity_threshold: minimum rule engine score to be considered confident
    ambiguity_threshold: float = float(os.getenv("AMBIGUITY_THRESHOLD", "2.0"))
    # unload_after_reasoning: free VRAM by unloading reasoning model after each use
    unload_after_reasoning: bool = os.getenv("UNLOAD_AFTER_REASONING", "true").lower() in ("true", "1", "yes")

    @property
    def allowed_origins(self) -> list[str]:
        return _parse_origins(self.allowed_origins_raw)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
