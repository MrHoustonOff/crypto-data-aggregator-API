from fastapi import FastAPI
from fastapi import APIRouter
from app.modules.rates.router import rates_router

app = FastAPI(
    title="Crypto Data Aggregator",
    version="0.0.1",
    description=(
        "An aggregator of cryptocurrency and fiat exchange rates with a price notification system.\n\n"
    )
)


v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(rates_router)

app.include_router(v1_router)


@app.get(
    "/health",
    summary="server status",
    tags=["system"],
    responses={
        200: {"description": "All dependencies are availible"},
        503: {"description": "One or many dependencies are unawailible"},
    },
)
async def health_check() -> dict:
    # TODO реализовать пинги к компонентам
    return {
        "status": "ok",
        "version": "0.0.1",
        "dependencies": {
            "postgres": "not_checked",
            "rabbitmq": "not_checked",
            "redis": "not_checked",
        },
    }
