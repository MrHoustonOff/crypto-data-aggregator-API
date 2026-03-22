from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database.session import get_db
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse, UserRegisterResponse
from app.modules.users.repositories import UserRepository
from app.modules.users.services import UserService
from app.modules.users.dependencies import CurrentUserDep
from app.core.rate_limit import RateLimiter, IPRateLimiter
import logging

users_router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: AsyncSession = Depends(get_db)):
    repository = UserRepository(session)
    return UserService(repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@users_router.post(
    "/register",
    summary="User registration",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(IPRateLimiter(requests=2, window=10))]
)
async def register_user(user_in: UserCreate, service: UserServiceDep):
    """Регистрация нового пользователя"""

    result = await service.register(user_in=user_in)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    new_user, raw_api_key = result

    return UserRegisterResponse(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        raw_api_key=raw_api_key
    )

@users_router.get(
    "/me",
    summary="Get current user info",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(requests=5, window=10))]
)
async def get_me(user: CurrentUserDep):
    """Возвращает информацию о текущем авторизованном пользователе"""
    return user