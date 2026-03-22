from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.alerts.models import DispatchLog, Alert

class DispatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(self, alert_id: str, status: str, attempt: int, response_code: int = None, error_msg: str = None):
        """
        Записывает попытку отправки вебхука в базу данных.
        """
        log_entry = DispatchLog(
            alert_id=alert_id,
            status=status,
            attempt=attempt,
            response_code=response_code,
            error_msg=error_msg
        )
        self.session.add(log_entry)
        await self.session.commit()

    async def deactivate_alert(self, alert_id: str):
        """
        Выключает алерт, если вебхук окончательно мертв.
        """
        stmt = (
            update(Alert)
            .where(Alert.id == alert_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
        await self.session.commit()