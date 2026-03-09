import logging
import os
from typing import List, Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    app_url: AnyHttpUrl = "http://localhost:8000"
    log_level: str = "INFO"
    tz: str = "Europe/Moscow"

    data_dir: str = "/app/data"
    kb_md_dir: str = "/app/rag_md_templates"

    jwt_secret: str = "CHANGE_ME_JWT_SECRET"
    cookie_secret: str = "CHANGE_ME_COOKIE_SECRET"

    postgres_db: str = "neuro_salesman"
    postgres_user: str = "neuro_user"
    postgres_password: str = "CHANGE_ME_DB_PASSWORD"
    database_url: str = (
        "postgresql+psycopg2://neuro_user:CHANGE_ME_DB_PASSWORD@db:5432/"
        "neuro_salesman"
    )

    telegram_bot_token: str = ""
    telegram_webhook_path: str = "/integrations/telegram/webhook"
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "CHANGE_ME_TELEGRAM_WEBHOOK_SECRET"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"

    rag_enabled: bool = False
    embedding_dim: int = 1536

    vite_api_base_url: str = "http://localhost:8000/api"
    frontend_public_url: Optional[AnyHttpUrl] = None

    reminder_enabled: bool = True
    reminder_hours_before: int = 24
    reminder_1_hours_before: int = 24
    reminder_2_hours_before: int = 2

    allowed_formats: str = "offline,online"
    allowed_time_prefs: str = "day,evening"
    day_start_hour: int = 9
    day_end_hour: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def telegram_mode(self) -> str:
        if self.telegram_webhook_url:
            return "webhook"
        return "polling"

    @property
    def allowed_origins(self) -> List[str]:
        origins: List[str] = []
        if self.app_env.lower() == "dev":
            origins.append("http://localhost:5173")
        origins.append(str(self.app_url))
        return origins

    @property
    def web_base_url(self) -> str:
        base = str(self.frontend_public_url or self.app_url)
        return base

    @property
    def web_url(self) -> str:
        base = self.web_base_url.rstrip("/")
        return f"{base}/web"

    @property
    def allowed_formats_list(self) -> List[str]:
        raw = self.allowed_formats or "offline,online"
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def allowed_time_prefs_list(self) -> List[str]:
        raw = self.allowed_time_prefs or "day,evening"
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

os.makedirs(settings.data_dir, exist_ok=True)
