from pydantic import BaseModel
from datetime import datetime


class RateResponse(BaseModel):
    ticker: str
    price_usdt: float
    updated_at: datetime
    
class RatesListResponse(BaseModel):
    data: list[RateResponse]
    cached: bool = True
    cache_ttl_sec: int | None = None