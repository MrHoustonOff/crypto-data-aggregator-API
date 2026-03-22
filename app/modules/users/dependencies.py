import hashlib
from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository
from app.database.redis import redis_client

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    api_key: str = Security(api_key_header),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    Проверяет API-ключ. Сначала ищет в Redis (кэш), если нет - идет в Postgres.
    """
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    cache_key = f"auth:{api_key_hash}"

    cached_user_id = await redis_client.get(cache_key)
    
    if cached_user_id:
        user = User()
        user.id = uuid.UUID(cached_user_id)
        return user

    repository = UserRepository(session)
    user = await repository.get_user_by_api_key(api_key_hash)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key"
        )
        
    await redis_client.set(cache_key, str(user.id), ex=3600) # 1 час

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
