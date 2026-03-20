from fastapi import APIRouter


rates_router = APIRouter(prefix="/rates", tags=["Rates"])


@rates_router.get(
    "",
    summary="Get all current exchange rates",
    responses={
        200: {"description": "Exchange rates list from cache"},
        429: {"description": "The rate limit has been exceeded"}
    }
)
async def get_rates(symbol: str | None):
    return {
        "rates": "rates list"
    }


@rates_router.get(
    "/{symbol}",
    summary="Get exchange rates of one pair",
    responses={
        200: {"description": "Pair exchange rates"},
        404: {"description": "Symbol not found in cache"},
        429: {"description": "The rate limit has been exceeded"}
    }
)
async def get_rate_by_symbol(symbol: str):
    return {
        "rates": f"rates list for {symbol}"
    }