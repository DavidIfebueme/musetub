from pydantic import BaseModel
from datetime import datetime


class FundTestnetResponse(BaseModel):
    wallet_address: str
    instructions: str
    docs_url: str


class ArcBlockHeightResponse(BaseModel):
    block_height: int


class UsdcBalanceResponse(BaseModel):
    wallet_address: str
    usdc_address: str
    balance_minor: int
    balance: str


class CircleTransactionResponse(BaseModel):
    id: str
    state: str
    tx_hash: str | None = None
    block_height: int | None = None
    error_reason: str | None = None
    error_details: str | None = None
    contract_address: str | None = None
    abi_function_signature: str | None = None
    ref_id: str | None = None
    wallet_id: str | None = None
    create_date: datetime | None = None
    update_date: datetime | None = None
