from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings

db_url = settings.db_url
_is_sqlite = db_url.startswith("sqlite")

_engine_kwargs = {"echo": False}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(db_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
