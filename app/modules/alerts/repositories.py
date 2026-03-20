from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.modules.alerts.models import Alert
from datetime import datetime
from sqlalchemy.sql import func


class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        user_id: UUID,
        ticker: str,
        target_price: float,
        condition: str,
        webhook_url: str,
    ) -> Alert | None:
        """Создает новый алерт с привязкой к конкретному пользователю."""
        new_alert = Alert(
            user_id=user_id,
            ticker=ticker.upper(),
            target_price=target_price,
            condition=condition,
            webhook_url=webhook_url,
        )
        self.session.add(new_alert)

        try:
            await self.session.commit()
            await self.session.refresh(new_alert)
            return new_alert
        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_user_alerts(self, user_id: UUID) -> list[Alert]:
        """Достает все алерты конкретного пользователя."""
        query = select(Alert).where(Alert.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_alert(self, alert_id: UUID, user_id: UUID) -> bool:
        """
        Возвращает True, если алерт удален, и False, если такого алерта нет (или он чужой).
        """
        query = delete(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def get_all_active_alerts(self) -> list[Alert]:
        """Достает ВСЕ активные алерты всех пользователей для воркера."""
        query = select(Alert).where(Alert.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def trigger_alert(self, alert_id: UUID) -> None:
        """Помечает алерт как сработавший."""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalars().first()

        if alert:
            alert.is_active = False

            alert.triggered_at = func.now()
            await self.session.commit()
