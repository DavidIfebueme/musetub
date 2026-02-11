from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[2] / ".env"),
            str(Path(__file__).resolve().parents[3] / ".env"),
            ".env",
        ),
        env_ignore_empty=True,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/musetub"
    redis_url: str = "redis://localhost:6379/0"


    ipfs_provider: str = "kubo"
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_gateway_url: str = "http://localhost:8080/ipfs"
    pinata_api_url: str = "https://api.pinata.cloud"
    pinata_jwt: str | None = None

    inference_api_key: str | None = None
    inference_base_url: str = "https://cluster-api.do-ai.run/v1"
    inference_model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"
    inference_vision_model: str = "meta-llama/Llama-3.2-90B-Vision-Instruct"
    inference_timeout_seconds: float = 30.0

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

    x402_network: str = "eip155:5042002"
    x402_max_timeout_seconds: int = 345600
    x402_gateway_sidecar_url: str | None = None
    x402_default_seller_address: str | None = None

    usdc_name: str = "USDC"
    usdc_version: str = "2"

    brevo_api_key: str | None = None
    brevo_sender_email: str | None = None
    brevo_sender_name: str = "MuseTub"
    contact_recipient_email: str | None = None


settings = Settings()
