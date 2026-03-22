import asyncio
import logging
import json

from app.workers.parser.service import ParserService
from app.workers.parser.adapters import BinanceAdapter, CoinGeckoAdapter
from app.core.config import settings
from app.database.redis import redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger("ParserWorker")

async def update_cache_with_prices(prices: dict[str, float]):
    """Сохраняет свежие цены в Redis."""
    if not prices:
        return
    try:
        prices_json = json.dumps(prices)
        await redis_client.set("current_rates", prices_json, ex=15)
        logger.info("Prices successfully cached in Redis.")
    except Exception as e:
         logger.error(f"Failed to cache prices in Redis: {e}")

async def main():
    logger.info("Starting Parser Worker...")

    parser = ParserService(
        adapters=[BinanceAdapter(), CoinGeckoAdapter()],
        tickers=settings.SUPPORTED_TICKERS
    )

    while True:
        try:
            logger.info("Fetching new prices...")
            prices = await parser.fetch_all_prices()
            
            if prices:
                await update_cache_with_prices(prices)
                logger.info(f"Result: {prices}")
            else:
                 logger.warning("No prices fetched in this cycle.")

        except Exception as e:
            logger.exception(f"Critical error in parser loop: {e}")

        # Спим 10 секунд
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Parser stopped manually.")