import asyncio
import logging
import httpx
import json

from app.database.session import async_session_factory
from app.modules.alerts.repositories import AlertRepository
from app.workers.parser.service import ParserService
from app.workers.parser.adapters import BinanceAdapter, CoinGeckoAdapter
from app.core.config import settings
from app.database.redis import redis_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("PriceWorker")

logging.getLogger("httpx").setLevel(logging.WARNING)


async def send_webhook(url: str, payload: dict):
    """
    Асинхронно отправляет вебхук.
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Sending webhook to {url}...")
            response = await client.post(url, json=payload, timeout=5.0)
            # В проде мы проверяем не просто отсутствие Exception, но и статус код
            response.raise_for_status()
            logger.info(f"Webhook success! URL: {url} | Status: {response.status_code}")
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Webhook HTTP error for {url}: Status {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Webhook connection failed for {url}: {e}")


async def update_cache_with_prices(prices: dict[str, float]):
    """
    Сохраняет свежие цены в Redis.
    """
    if not prices:
        return
    try:
        prices_json = json.dumps(prices)
        await redis_client.set("current_rates", prices_json, ex=15)
        logger.debug("Prices successfully cached in Redis.")
    except Exception as e:
        logger.error(f"Failed to cache prices in Redis: {e}")


async def process_active_alerts(prices: dict[str, float]):
    """
    Достает алерты из БД, проверяет условия и запускает отправку вебхуков.
    """
    async with async_session_factory() as session:
        repo = AlertRepository(session)
        active_alerts = await repo.get_all_active_alerts()

        if not active_alerts:
            return

        triggered_count = 0

        for alert in active_alerts:
            current_price = prices.get(alert.ticker)
            if not current_price:
                continue

            target = float(alert.target_price)
            is_triggered = False

            if alert.condition == "gt" and current_price > target:
                is_triggered = True
            elif alert.condition == "lt" and current_price < target:
                is_triggered = True

            if is_triggered:
                logger.warning(
                    f"🚨 ALERT TRIGGERED: {alert.ticker} | Current: {current_price} | Target: {alert.target_price} ({alert.condition})"
                )

                await repo.trigger_alert(alert.id)
                triggered_count += 1

                payload = {
                    "alert_id": str(alert.id),
                    "ticker": alert.ticker,
                    "price": current_price,
                    "condition": alert.condition,
                    "message": "Price target reached!",
                }
                asyncio.create_task(send_webhook(alert.webhook_url, payload))

        if triggered_count > 0:
            logger.info(f"Processed and triggered {triggered_count} alerts.")


async def main():
    logger.info("Starting Price Checker Worker...")

    parser = ParserService(
        adapters=[BinanceAdapter(), CoinGeckoAdapter()],
        tickers=settings.SUPPORTED_TICKERS,
    )

    while True:
        try:
            logger.info("Fetching new prices...")
            prices = await parser.fetch_all_prices()

            if prices:
                await update_cache_with_prices(prices)

                await process_active_alerts(prices)
            else:
                logger.warning("No prices fetched in this cycle.")

        except Exception as e:
            logger.exception(f"Critical error in main worker loop: {e}")

        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually.")
