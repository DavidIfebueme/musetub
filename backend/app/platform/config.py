from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[3] / ".env"),
            ".env",
        ),
        env_ignore_empty=True,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/musetub"
    redis_url: str = "redis://localhost:6379/0"
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_gateway_url: str = "http://localhost:8080/ipfs"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 10.0
    gemini_max_prompt_chars: int = 2500

    jwt_secret: str = "dev-unsafe-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 43200
    allowed_origins: str = "http://localhost:3000"

    circle_api_key: str | None = None
    circle_entity_secret: str | None = None
    circle_wallet_set_id: str | None = None
    circle_environment: str = "sandbox"
    circle_blockchain: str = "ARC-TESTNET"

    arc_rpc_url: str | None = None
    arc_chain_id: int | None = None
    usdc_address: str | None = None
    escrow_address: str | None = None

    usdc_name: str = "USD Coin"
    usdc_version: str = "2"


settings = Settings()
