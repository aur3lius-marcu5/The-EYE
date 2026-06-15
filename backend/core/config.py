from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./the_eye.db"
    groq_api_key_1: str = ""
    groq_api_key_2: str = ""
    openrouter_api_key_1: str = ""
    openrouter_api_key_2: str = ""
    ai_provider_priority: str = "groq,openrouter,template"
    nmap_path: str = "auto"
    masscan_path: str = "auto"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    api_key: str = ""
    heartbeat_seconds: int = 30
    pipeline_max_new_targets: int = 50
    pipeline_max_depth: int = 2
    pipeline_passive_only_default: bool = True


settings = Settings()
