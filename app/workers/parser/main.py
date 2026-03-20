import asyncio
import logging
import httpx

from app.database.session import async_session_factory
from app.modules.alerts.repositories import AlertRepository

from app.workers.parser.service import ParserService
from app.workers.parser.adapters import BinanceAdapter, CoinGeckoAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Worker")


async def send_webhook(url: str, payload: dict):
    """
    Асинхронно отправляет вебхук.
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Sending webhook to {url}...")
            response = await client.post(url, json=payload, timeout=5.0)
            logger.info(f"Webhook success! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Webhook failed for {url}: {e}")


async def main():
    logger.info("Starting Price Checker Worker...")
    
    parser = ParserService(
        adapters=[BinanceAdapter(), CoinGeckoAdapter()],
        tickers=["BTC", "ETH", "DOGE", "SOL", "BNB"] # TODO заполнять через конфиг.
    )

    while True:
        try:
            prices = await parser.fetch_all_prices()
            logger.info(f"Fetched prices: {prices}")

            async with async_session_factory() as session:
                repo = AlertRepository(session)
                
                active_alerts = await repo.get_all_active_alerts()
                if active_alerts:
                    logger.info(f"Checking {len(active_alerts)} active alerts...")

                for alert in active_alerts:
                    current_price = prices.get(alert.ticker)
                    
                    if not current_price:
                        continue

                    is_triggered = False
                    if alert.condition == "gt" and current_price > alert.target_price:
                        is_triggered = True
                    elif alert.condition == "lt" and current_price < alert.target_price:
                        is_triggered = True

                    if is_triggered:
                        logger.warning(f"🚨 ALERT TRIGGERED: {alert.ticker} is {current_price} (Target: {alert.target_price})")
                        
                        await repo.trigger_alert(alert.id)
                        
                        payload = {
                            "alert_id": str(alert.id),
                            "ticker": alert.ticker,
                            "price": current_price,
                            "condition": alert.condition,
                            "message": f"Price target reached!"
                        }
                        
                        asyncio.create_task(send_webhook(alert.webhook_url, payload))

        except Exception as e:
            logger.error(f"Critical error in worker loop: {e}")

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())