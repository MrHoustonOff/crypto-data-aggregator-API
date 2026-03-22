import asyncio
import logging
import json
import aio_pika

from app.core.config import settings
from app.workers.sender.service import process_webhook_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger("SenderWorker")

async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    """
    Обработчик одного сообщения из очереди.
    """
    async with message.process(): 
        body = message.body.decode()
        task_data = json.loads(body)
        
        logger.info(f"Received task for alert: {task_data.get('alert_id')} ({task_data.get('ticker')})")
        
        await process_webhook_task(task_data)

async def main():
    logger.info("Starting Webhook Sender Worker...")
    
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        
        await channel.set_qos(prefetch_count=10)
        
        queue = await channel.declare_queue("webhooks_queue", durable=True)
        
        logger.info("Sender is listening to 'webhooks_queue'...")
        
        await queue.consume(process_message)
        
        logger.info("Waiting for messages. To exit press CTRL+C")
        await asyncio.Future() 

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sender stopped manually.")