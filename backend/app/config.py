from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cups_server: str = "http://localhost:631"
    cups_user: str = ""
    cups_password: str = ""
    print_api_key: str = "change-this-key"
    admin_username: str = "admin"
    admin_password: str = "change-this-password"
    max_upload_size_mb: int = 50
    poll_interval_seconds: int = 5
    cors_origins: str = "http://localhost:8080"
    tz: str = "UTC"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
