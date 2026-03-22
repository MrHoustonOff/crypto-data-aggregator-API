import logging
import httpx
from tenacity import RetryError
from app.database.session import async_session_factory
from app.workers.sender.http_client import send_webhook_with_retries
from app.workers.sender.repository import DispatchRepository

logger = logging.getLogger("Sender.Service")

async def process_webhook_task(task_data: dict):
    alert_id = task_data.get("alert_id")
    webhook_url = task_data.get("webhook_url")
    
    payload_to_send = {
        "alert_id": alert_id,
        "ticker": task_data.get("ticker"),
        "price": task_data.get("price"),
        "condition": task_data.get("condition"),
        "message": task_data.get("message")
    }

    status = "failed"
    response_code = None
    error_msg = None
    attempt = 1 # Для MVP пишем просто 1, Tenacity скрывает от нас внутренние попытки

    try:
        response = await send_webhook_with_retries(webhook_url, payload_to_send)
        status = "success"
        response_code = response.status_code
        logger.info(f"Webhook sent successfully for alert {alert_id}")
        
    except httpx.HTTPStatusError as e:
        response_code = e.response.status_code
        error_msg = f"HTTP Error: {response_code}"
        logger.error(f"Failed to send webhook for alert {alert_id} after retries: {error_msg}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Critical failure sending webhook for alert {alert_id}: {error_msg}")
    
    try:
        async with async_session_factory() as session:
            repo = DispatchRepository(session)
            await repo.create_log(
                alert_id=alert_id, 
                status=status, 
                attempt=attempt,
                response_code=response_code, 
                error_msg=error_msg
            )
            if status == "failed":
                await repo.deactivate_alert(alert_id)
                logger.warning(f"Alert {alert_id} deactivated due to dead webhook.")
                
    except Exception as e:
        logger.error(f"Failed to save dispatch log to DB: {e}")