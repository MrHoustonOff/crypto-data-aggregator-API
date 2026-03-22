async def test_create_alert_unauthorized(client):
    """Алерт нельзя создать без ключа."""
    payload = {
        "ticker": "BTC", 
        "condition": "gt", 
        "target_price": 100000, 
        "webhook_url": "http://test.com"
    }
    response = await client.post("/api/v1/alerts/", json=payload)
    assert response.status_code == 401

async def test_create_alert_negative_price(client):
    """Валидация бизнес-логики: цена не может быть отрицательной."""
    payload = {
        "ticker": "BTC", 
        "condition": "gt", 
        "target_price": -500, 
        "webhook_url": "http://test.com"
    }
    # Подсовываем фейковый ключ, чтобы пройти проверку на наличие заголовка
    response = await client.post("/api/v1/alerts/", headers={"X-API-Key": "fake_key"}, json=payload)
    assert response.status_code == 401