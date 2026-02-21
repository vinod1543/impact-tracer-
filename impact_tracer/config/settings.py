"""Application settings model for Impact Tracer."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"
    demo_mode: int = 0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
