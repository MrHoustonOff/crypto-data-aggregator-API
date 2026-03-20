import hashlib
from app.modules.users.repositories import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.users.models import User


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def _hash_api_key(self, api_key: str) -> str:
        """Внутренний метод для хеширования"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def register(self, user_in: UserCreate) -> User | None:
        """
        Бизнес-логика регистрации.
        Хеширует пароль и передает данные на слой БД.
        """
        hashed_key = self._hash_api_key(user_in.api_key)

        return await self.repository.create_user(
            email=user_in.email, api_key_hash=hashed_key
        )
