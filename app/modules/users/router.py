from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database.session import get_db
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.repositories import UserRepository
from app.modules.users.services import UserService

users_router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: AsyncSession = Depends(get_db)):
    repository = UserRepository(session)
    return UserService(repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@users_router.post(
    "/register",
    summary="User registration",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_in: UserCreate, service: UserServiceDep):
    """Регистрация нового пользователя"""

    new_user = await service.register(user_in=user_in)
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    return new_user
