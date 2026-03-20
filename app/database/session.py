from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from app.core.config import settings

engine: AsyncEngine = create_async_engine(settings.database_url)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    echo=True
)

async def get_db():
    async with async_session_factory() as session:
        yield session
    