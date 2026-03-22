import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("Sender.HTTP")

@retry(
    stop=stop_after_attempt(4), 
    wait=wait_exponential(multiplier=10, min=10, max=600),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def send_webhook_with_retries(url: str, payload: dict) -> httpx.Response:
    # Отключаем проверку SSL (verify=False) специально для локальных тестов
    # В проде это надо убрать!
    async with httpx.AsyncClient(verify=False) as client:
        logger.debug(f"Attempting to send webhook to {url}")
        response = await client.post(url, json=payload, timeout=5.0)
        response.raise_for_status() 
        return response