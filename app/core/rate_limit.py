from fastapi import HTTPException, status, Depends, Request
from redis.asyncio import Redis

from app.database.redis import get_redis
from app.modules.users.dependencies import CurrentUserDep


class RateLimiter:
    """
    Класс-зависимость для ограничения количества запросов.
    """

    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, user: CurrentUserDep, redis: Redis = Depends(get_redis)):
        key = f"rate_limit:{user.id}"

        current = await redis.incr(key)

        if current == 1:
            await redis.expire(key, self.window)

        # Если лимит превышен, бьем по рукам
        if current > self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests} requests per {self.window} seconds.",
            )


class IPRateLimiter:
    """
    Лимитер для публичных эндпоинтов. Считает запросы по IP клиента.
    """

    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request, redis: Redis = Depends(get_redis)):
        # Достаем IP-адрес из запроса
        client_ip = request.client.host if request.client else "unknown_ip"
        key = f"rate_limit:ip:{client_ip}"

        current = await redis.incr(key)

        if current == 1:
            await redis.expire(key, self.window)

        if current > self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests} requests per {self.window} seconds.",
            )
