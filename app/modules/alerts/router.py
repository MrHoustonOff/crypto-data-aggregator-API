from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.users.dependencies import CurrentUserDep
from app.modules.alerts.schemas import AlertCreate, AlertResponse
from app.modules.alerts.repositories import AlertRepository
from app.modules.alerts.services import AlertService
from app.core.rate_limit import RateLimiter

alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_alert_service(session: AsyncSession = Depends(get_db)) -> AlertService:
    repository = AlertRepository(session)
    return AlertService(repository)


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]


@alerts_router.post(
    "/",
    summary="Create a new alert",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(requests=6, window=60))]
)
async def create_alert(
    alert_in: AlertCreate,
    user: CurrentUserDep,
    service: AlertServiceDep,
):  
    new_alert = await service.create_alert(user_id=user.id, alert_in=alert_in)
    
    if not new_alert:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active alert with exactly the same parameters."
        )
        
    return new_alert


@alerts_router.get(
    "/",
    summary="Get all user`s alerts",
    response_model=list[AlertResponse],
    dependencies=[Depends(RateLimiter(requests=20, window=60))]
)
async def get_alerts(user: CurrentUserDep, service: AlertServiceDep):
    return await service.get_user_alerts(user_id=user.id)


@alerts_router.delete(
    "/{alert_id}",
    summary="Delete an alert",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(requests=20, window=60))]
)
async def delete_alert(alert_id: UUID, user: CurrentUserDep, service: AlertServiceDep):
    is_deleted = await service.delete_alert(alert_id=alert_id, user_id=user.id)

    if not is_deleted:
        # Мы кидаем 404 Not Found, чтобы не подсказывать хакерам, существуют ли чужие алерты с таким ID.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )
