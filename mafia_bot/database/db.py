"""
PostgreSQL bilan async ulanish va session factory.
"""
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import DATABASE_URL, DATABASE_SSL
from database.models import Base

logger = logging.getLogger(__name__)

_engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)
    if DATABASE_SSL:
        # asyncpg SSL parametrni query-string orqali emas, connect_args orqali kutadi
        _engine_kwargs["connect_args"] = {"ssl": True}

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Bot birinchi marta ishga tushganda barcha jadvallarni yaratadi."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as e:
        logger.error(
            "PostgreSQL bazasiga ulanib bo'lmadi. DATABASE_URL to'g'ri ekanini "
            "(host, port, parol, DATABASE_SSL) va Railway'dagi Postgres servisi "
            "ishga tushganini tekshiring. Xatolik: %s", e
        )
        raise
