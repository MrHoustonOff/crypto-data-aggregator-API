import uuid

async def test_ip_rate_limiter_blocks_spam(client):
    """Проверка алгоритма Rate Limit (блокировка после N запросов)."""
    # Делаем 2 разрешенных запроса
    for _ in range(2):
        await client.post(
            "/api/v1/users/register", 
            json={"email": f"spam_{uuid.uuid4().hex[:6]}@example.com"}
        )
    
    # 3-й запрос должен отбиться с 429 Too Many Requests
    response = await client.post(
        "/api/v1/users/register", 
        json={"email": "block_me@example.com"}
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]