import uuid

async def test_register_user_success(client):
    """Проверка генерации API-ключа при регистрации."""
    test_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    response = await client.post("/api/v1/users/register", json={"email": test_email})
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_email
    assert "raw_api_key" in data
    assert data["raw_api_key"].startswith("sk_live_")

async def test_register_validation_error(client):
    """Проверка 422 ошибки при неверном email."""
    response = await client.post("/api/v1/users/register", json={"email": "invalid-email"})
    
    assert response.status_code == 422
    assert response.json()["error"] == "ValidationError"

async def test_auth_missing_api_key(client):
    """Проверка 401 ошибки при отсутствии X-API-Key."""
    response = await client.get("/api/v1/users/me")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API Key in headers"