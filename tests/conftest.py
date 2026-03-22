import pytest
from fastapi.testclient import TestClient
from fakeredis.aioredis import FakeRedis

from app.main import app
from app.database.redis import get_redis

@pytest.fixture
def fake_redis_client():
    return FakeRedis(decode_responses=True)

@pytest.fixture
def client(fake_redis_client):
    app.dependency_overrides[get_redis] = lambda: fake_redis_client
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()