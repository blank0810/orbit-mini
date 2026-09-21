from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# This is the only module that reads the environment.
class Settings(BaseSettings):
    database_url: str
    cors_origins: str = ""
    environment: str = "development"
    jwt_secret: str = "dev-only-insecure-change-me"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days; there is no refresh flow.
    plan_name: str = "ScaleSage Starter"
    cookie_name: str = "orbit_session"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cookie_secure(self) -> bool:
        # Secure is derived from the environment, not a separate switch, so it cannot
        # be set inconsistently.
        return self.environment != "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
