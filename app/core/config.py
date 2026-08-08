"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import dotenv_values


def _load_dotenv_overrides() -> dict[str, str]:
    """Load .env file values — these take priority over system env vars."""
    env_path = Path(".env")
    if not env_path.exists():
        # Try from project root
        env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        values = dotenv_values(env_path)
        return {k: v for k, v in values.items() if v is not None}
    return {}


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    # LLM Configuration
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str = ""
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: int = 30

    # Embedding Configuration
    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Interview Configuration
    min_questions: int = 8
    target_questions: int = 10
    max_questions: int = 15
    min_curriculum_days: int = 4
    question_similarity_threshold: float = 0.85

    # Vector DB
    vector_db_provider: str = "memory"
    vector_db_url: str = ""

    # Redis
    redis_url: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        # Load .env values with priority over process env vars
        overrides = _load_dotenv_overrides()
        # Convert keys to lowercase to match pydantic field names
        overrides_lower = {k.lower(): v for k, v in overrides.items()}
        _settings = Settings(**overrides_lower)
    return _settings
