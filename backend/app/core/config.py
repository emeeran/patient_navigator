"""Application configuration loaded from environment variables."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_DEFAULT = "change-me-in-production-min-32-chars!!"


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
    JWT_SECRET_KEY: str = _INSECURE_JWT_DEFAULT
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

    # Cloud AI fallback providers (keys set = provider enabled)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_AI_API_KEY: str = ""
    GOOGLE_AI_MODEL: str = "gemini-2.0-flash"

    # Provider order for fallback chain
    AI_PROVIDER_ORDER: str = "ollama,groq,google"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @model_validator(mode="after")
    def _validate_production_settings(self) -> "Settings":
        """Prevent the app from starting with insecure defaults in production."""
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.JWT_SECRET_KEY == _INSECURE_JWT_DEFAULT:
            errors.append(
                "JWT_SECRET_KEY must be changed from its default value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if self.DEBUG:
            errors.append("DEBUG must be False in production")
        if self.BCRYPT_ROUNDS < 10:
            errors.append("BCRYPT_ROUNDS must be >= 10 in production")
        if "*" in self.cors_origins_list or any(
            "localhost" in o for o in self.cors_origins_list
        ):
            errors.append(
                "CORS_ORIGINS must not contain '*' or 'localhost' in production"
            )

        if errors:
            raise ValueError(
                "Production environment validation failed:\n  - "
                + "\n  - ".join(errors)
            )
        return self


settings = Settings()
