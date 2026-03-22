import hashlib
import secrets
from app.modules.users.repositories import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.models import User


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def _hash_api_key(self, api_key: str) -> str:
        """Внутренний метод для хеширования"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def register(self, user_in: UserCreate) -> tuple[User, str] | None:
        """
        Бизнес-логика регистрации.
        Генерирует надежный API-ключ, хеширует его и сохраняет в БД.
        Возвращает кортеж: (User, raw_api_key).
        """
        # Генерируем уникальный ключ на 32 байта (url-safe)
        raw_api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        # Хешируем его для базы
        hashed_key = self._hash_api_key(raw_api_key)

        new_user = await self.repository.create_user(
            email=user_in.email, api_key_hash=hashed_key
        )
        
        if not new_user:
            return None
            
        return new_user, raw_api_key