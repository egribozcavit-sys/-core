from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "PayCore"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str
    REDIS_URL: str
    REDIS_STREAM_NAME: str = "paycore:transactions"
    REDIS_CONSUMER_GROUP: str = "paycore-workers"

    MAX_WORKERS: int = 4
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    REDIS_POOL_SIZE: int = 10
    BATCH_SIZE: int = 100

    RATE_LIMIT_PER_MINUTE: int = 1000

    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
