from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POD_", env_file="config/.env", extra="ignore")

    database_url: str = "postgresql+psycopg://pod:pod@localhost:5432/pod"
    jwt_secret: str = "dev-secret-change-me-at-least-32-bytes"
    model_storage_dir: str = "var/model_files"
    upload_limit: int = 10
    upload_limit_period_days: int | None = None
