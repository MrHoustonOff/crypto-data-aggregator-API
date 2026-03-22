import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя (то, что принимаем от клиента)"""

    email: EmailStr


class UserResponse(BaseModel):
    """Схема для ответа (то, что отдаем клиенту)"""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserRegisterResponse(UserResponse):
    """Схема ответа ТОЛЬКО при регистрации. Содержит сырой API ключ!"""
    raw_api_key: str