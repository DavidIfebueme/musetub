from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://musetub:change-me@localhost:5433/musetub"
    redis_url: str = "redis://localhost:6380/0"
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_gateway_url: str = "http://localhost:8080/ipfs"

    jwt_secret: str = "change-me"
    allowed_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
