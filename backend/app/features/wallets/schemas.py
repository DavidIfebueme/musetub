from pydantic import BaseModel


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
