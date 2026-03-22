import asyncio
import logging
import json

from app.database.session import async_session_factory
from app.modules.alerts.repositories import AlertRepository
from app.database.redis import redis_client
from app.database.rabbitmq import rabbitmq_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger("CheckerWorker")

async def process_active_alerts():
    """
    Берет цены из Редиса, алерты из БД, проверяет и кидает задачи в очередь.
    """
    rates_json = await redis_client.get("current_rates")
    if not rates_json:
        logger.warning("No prices in Redis. Waiting for Parser...")
        return

    prices = json.loads(rates_json)

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
                    f"ALERT TRIGGERED: {alert.ticker} | Current: {current_price} | Target: {alert.target_price}"
                )
                
                await repo.trigger_alert(alert.id)
                triggered_count += 1

                payload = {
                    "alert_id": str(alert.id),
                    "ticker": alert.ticker,
                    "price": current_price,
                    "condition": alert.condition,
                    "webhook_url": alert.webhook_url,
                    "message": "Price target reached!",
                }
                
                await rabbitmq_client.publish_webhook_task(payload)
        
        if triggered_count > 0:
             logger.info(f"Pushed {triggered_count} tasks to RabbitMQ.")


async def main():
    logger.info("Starting Checker Worker...")
    
    await rabbitmq_client.connect()

    try:
        while True:
            try:
                await process_active_alerts()
            except Exception as e:
                logger.exception(f"Critical error in checker loop: {e}")

            await asyncio.sleep(10)
    finally:
        await rabbitmq_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Checker stopped manually.")