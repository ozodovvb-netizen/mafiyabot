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
            await conn.run_sync(_add_missing_columns)
    except SQLAlchemyError as e:
        logger.error(
            "PostgreSQL bazasiga ulanib bo'lmadi. DATABASE_URL to'g'ri ekanini "
            "(host, port, parol, DATABASE_SSL) va Railway'dagi Postgres servisi "
            "ishga tushganini tekshiring. Xatolik: %s", e
        )
        raise


def _add_missing_columns(sync_conn):
    """`Base.metadata.create_all` faqat YANGI jadvallarni yaratadi -- agar jadval allaqachon
    mavjud bo'lsa (masalan, bot avval boshqa versiyada ishga tushirilgan bo'lsa), yangi
    qo'shilgan ustunlarni (masalan roles.mode, roles.game_mode_id) hech qachon o'zi
    qo'shmaydi. Shu sabab ba'zi so'rovlar "column ... does not exist" xatoligi bilan jim
    ichida qulab tushib, foydalanuvchiga hech narsa ko'rinmasligi mumkin edi (masalan
    guruhda /start bilan o'yin "boshlandi" deyilib, aslida start_game() xatolik berib
    to'xtab qolardi). Shu funksiya har bir jadvaldagi yetishmayotgan ustunlarni avtomatik
    ALTER TABLE ... ADD COLUMN bilan qo'shib qo'yadi.
    """
    import sqlalchemy as sa

    inspector = sa.inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # yangi jadval - create_all allaqachon yaratdi
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            try:
                col_type = column.type.compile(dialect=sync_conn.dialect)
                default_sql = ""
                if column.default is not None and getattr(column.default, "arg", None) is not None and not callable(column.default.arg):
                    default_sql = f" DEFAULT {column.default.arg!r}" if isinstance(column.default.arg, str) else f" DEFAULT {column.default.arg}"
                nullable_sql = "" if column.nullable else " NOT NULL" if not default_sql else ""
                sync_conn.execute(sa.text(
                    f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}{default_sql}{nullable_sql}'
                ))
                logger.warning(
                    "Baza jadvali '%s' ga yetishmayotgan ustun '%s' avtomatik qo'shildi.",
                    table.name, column.name,
                )
            except Exception as e:
                logger.error(
                    "Jadval '%s' ustun '%s' ni qo'shishda xatolik: %s", table.name, column.name, e
                )
