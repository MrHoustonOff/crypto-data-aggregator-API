import json
import logging
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from app.core.config import settings

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractRobustChannel | None = None

    async def connect(self):
        """
        Открывает соединение один раз при старте приложения/воркера.
        """
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            await self.channel.declare_queue("webhooks_queue", durable=True)
            logger.info("RabbitMQ connection established and queue declared.")

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed.")

    async def publish_webhook_task(self, payload: dict):
        if not self.channel:
            raise RuntimeError("RabbitMQ client is not connected! Call connect() first.")
            
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT 
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key="webhooks_queue"
        )

rabbitmq_client = RabbitMQClient()