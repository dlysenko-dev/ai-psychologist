"""AI Psychologist — Configuration"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_psychologist",
        env="DATABASE_URL",
    )

    # AI (OpenClaw gateway — OpenAI-compatible proxy)
    openclaw_gateway_url: str = Field(
        default="http://127.0.0.1:18789/v1", env="OPENCLAW_GATEWAY_URL"
    )
    openclaw_gateway_token: str = Field(default="", env="OPENCLAW_GATEWAY_TOKEN")
    ai_model: str = Field(default="claude-sonnet-4-20250514", env="AI_MODEL")
    ai_fallback_model: str = Field(
        default="claude-sonnet-4-20250514", env="AI_FALLBACK_MODEL"
    )

    # Telegram
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    mini_app_url: str = Field(default="", env="MINI_APP_URL")
    admin_telegram_id: int = Field(default=756877849, env="ADMIN_TELEGRAM_ID")

    # Auth
    app_secret_key: str = Field(default="change-me", env="APP_SECRET_KEY")

    # Server
    backend_port: int = Field(default=8010, env="BACKEND_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
