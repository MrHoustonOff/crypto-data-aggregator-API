import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fakeredis.aioredis import FakeRedis

from app.main import app
import app.database.redis as db_redis

@pytest_asyncio.fixture(scope="session")
async def fake_redis_client():
    """Фейковый in-memory Redis, живет одну сессию для всех тестов."""
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()

@pytest_asyncio.fixture(autouse=True)
async def clear_redis(fake_redis_client):
    """Сбрасываем кэш и счетчики Rate Limit перед каждым тестом."""
    await fake_redis_client.flushall()

@pytest_asyncio.fixture(scope="session")
async def client(fake_redis_client):
    """Асинхронный HTTP-клиент FastAPI."""
    original_redis = db_redis.redis_client
    db_redis.redis_client = fake_redis_client
    
    if hasattr(db_redis, "get_redis"):
        app.dependency_overrides[db_redis.get_redis] = lambda: fake_redis_client
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    db_redis.redis_client = original_redis
    app.dependency_overrides.clear()