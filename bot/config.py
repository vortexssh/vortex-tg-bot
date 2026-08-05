from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    core_url: str = "http://localhost:8000/api/v1"
    bot_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
