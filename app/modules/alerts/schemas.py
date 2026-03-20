import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, field_validator
from app.core.config import settings


class AlertCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    target_price: float = Field(..., gt=0)
    condition: Literal["gt", "lt"] = Field(...)
    webhook_url: HttpUrl = Field(...)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in settings.SUPPORTED_TICKERS:
            raise ValueError(
                f"Yo, we don't support '{v_upper}'! Supported coins: {', '.join(settings.SUPPORTED_TICKERS)}"
            )
        return v_upper


class AlertResponse(BaseModel):

    id: uuid.UUID
    user_id: uuid.UUID
    ticker: str
    target_price: float
    condition: str
    webhook_url: str
    is_active: bool
    created_at: datetime
    triggered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
