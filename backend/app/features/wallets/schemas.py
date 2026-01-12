from pydantic import BaseModel


class FundTestnetResponse(BaseModel):
    wallet_address: str
    instructions: str
    docs_url: str
