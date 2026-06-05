"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. All values are overridden by .env or environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────
    APP_NAME: str = "Patient Navigator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://navigator:navigator_dev@localhost:5432/patient_nav"
    DATABASE_URL_SYNC: str = "postgresql://navigator:navigator_dev@localhost:5432/patient_nav"

    # ── Redis ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-min-32-chars!!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Security ─────────────────────────────────────
    BCRYPT_ROUNDS: int = 12
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 600

    # ── CORS ─────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── File Upload / Document Storage ────────────────────────
    UPLOAD_DIR: str = "./uploads/documents"
    MAX_UPLOAD_SIZE_BYTES: int = 26_214_400  # 25MB

    # ── AI / LLM ────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "medgemma:4b"
    OLLAMA_TIMEOUT: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
