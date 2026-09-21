from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# This is the only module that reads the environment.
class Settings(BaseSettings):
    database_url: str
    cors_origins: str = ""
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
