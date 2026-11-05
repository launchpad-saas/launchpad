from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@core_api_db:5432/launchpad_core"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    LOG_LEVEL: str = "INFO"


settings = Settings()