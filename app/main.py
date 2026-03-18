from fastapi import FastAPI


app = FastAPI(
    title="Crypto Data Aggregator",
    version="0.0.1",
    description=(
        "An aggregator of cryptocurrency and fiat exchange rates with a price notification system.\n\n"
    )
)


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
