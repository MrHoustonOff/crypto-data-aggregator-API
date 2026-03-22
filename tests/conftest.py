import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fakeredis.aioredis import FakeRedis

from app.main import app
import app.database.redis as db_redis

@pytest_asyncio.fixture
async def fake_redis_client():
    """Фейковый in-memory Redis, изолированный для каждого теста"""
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()

@pytest_asyncio.fixture
async def client(fake_redis_client):
    # 1. Жестко подменяем глобальный клиент Редиса
    original_redis = db_redis.redis_client
    db_redis.redis_client = fake_redis_client
    
    # 2. Подменяем зависимость (если она используется в Rate Limiter)
    if hasattr(db_redis, "get_redis"):
        app.dependency_overrides[db_redis.get_redis] = lambda: fake_redis_client
        
    # 3. Запускаем асинхронного клиента
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    # Восстанавливаем всё как было
    db_redis.redis_client = original_redis
    app.dependency_overrides.clear()