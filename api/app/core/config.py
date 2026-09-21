from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# This is the only module that reads the environment.
class Settings(BaseSettings):
    database_url: str
    cors_origins: str = ""
    # Defaults to production. A missing ENVIRONMENT must yield the STRICTER behaviour:
    # forgetting to set it in a deployment cannot silently disable the Secure cookie flag.
    # Development opts in explicitly.
    environment: str = "production"
    # No default, and a length floor. A committed fallback secret would let anyone who
    # reads this repository forge a session cookie for any subscriber id, and this service
    # is published to the internet through a tunnel. Missing or weak fails startup loudly.
    # Generate with: openssl rand -hex 32
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days; there is no refresh flow.
    plan_name: str = "ScaleSage Starter"
    cookie_name: str = "orbit_session"
    # jwt_secret has no default: a default signing key makes sessions forgeable, a live
    # vulnerability. An empty Stripe API key has no security consequence: it cannot call
    # Stripe. Fail clearly at the point of use so non-payment features can still start.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""
    web_base_url: str = "http://localhost:7301"

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
