from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.modules.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, email: str, api_key_hash: str) -> User | None:
        """
        Пытается создать юзера. Если email занят, откатывает транзакцию и возвращает None.
        """
        new_user = User(email=email, api_key_hash=api_key_hash)
        self.session.add(new_user)

        try:
            await self.session.commit()
            await self.session.refresh(new_user)
            return new_user
        except IntegrityError:
            await self.session.rollback()
            return None
