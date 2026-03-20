from uuid import UUID
from app.modules.alerts.repositories import AlertRepository
from app.modules.alerts.schemas import AlertCreate
from app.modules.alerts.models import Alert


class AlertService:
    def __init__(self, repository: AlertRepository):
        self.repository = repository

    async def create_alert(self, user_id: UUID, alert_in: AlertCreate) -> Alert:
        webhook_str = str(alert_in.webhook_url)

        return await self.repository.create_alert(
            user_id=user_id,
            ticker=alert_in.ticker,
            target_price=alert_in.target_price,
            condition=alert_in.condition,
            webhook_url=webhook_str,
        )

    async def get_user_alerts(self, user_id: UUID) -> list[Alert]:
        """
        Получение всех алертов пользователя.
        """
        return await self.repository.get_user_alerts(user_id=user_id)

    async def delete_alert(self, alert_id: UUID, user_id: UUID) -> bool:
        """
        Удаление алерта.
        """
        return await self.repository.delete_alert(alert_id=alert_id, user_id=user_id)
