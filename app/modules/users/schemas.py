import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя (то, что принимаем от клиента)"""

    email: EmailStr
    api_key: str = Field(min_leangth=8, max_leangth=150)


class UserResponse(BaseModel):
    """Схема для ответа (то, что отдаем клиенту)"""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
