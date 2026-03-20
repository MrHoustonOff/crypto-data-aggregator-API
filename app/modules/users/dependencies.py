import hashlib
from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    api_key: str = Security(api_key_header), session: AsyncSession = Depends(get_db)
) -> User:
    """
    Хеширует входящий ключ, ищет юзера и проверяет статус аккаунта.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' header",
        )

    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

    repo = UserRepository(session)
    user = await repo.get_user_by_api_key(hashed_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
