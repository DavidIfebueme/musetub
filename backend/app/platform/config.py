from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://musetub:change-me@localhost:5433/musetub"
    redis_url: str = "redis://localhost:6380/0"
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_gateway_url: str = "http://localhost:8080/ipfs"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 10.0
    gemini_max_prompt_chars: int = 2500

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 43200
    allowed_origins: list[str] = ["http://localhost:3000"]

    circle_api_key: str | None = None
    circle_entity_secret: str | None = None
    circle_wallet_set_id: str | None = None
    circle_environment: str = "sandbox"


settings = Settings()
