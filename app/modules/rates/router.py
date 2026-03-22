import json
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from app.database.redis import get_redis
from app.modules.users.dependencies import CurrentUserDep
from app.core.rate_limit import RateLimiter

rates_router = APIRouter(prefix="/rates", tags=["Rates"])


@rates_router.get(
    "/",
    summary="Get current cryptocurrency rates",
    description="Returns the latest prices fetched from exchanges. Data is cached in Redis for lightning-fast responses.",
    dependencies=[Depends(RateLimiter(requests=10, window=10))]
)
async def get_current_rates(user: CurrentUserDep, redis: Redis = Depends(get_redis)):
    """
    Получение текущих курсов валют из кэша.
    """
    rates_json = await redis.get("current_rates")

    if not rates_json:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rates are currently warming up. Please try again in a few seconds.",
        )

    return json.loads(rates_json)
