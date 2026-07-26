"""Turli joylarda ishlatiladigan kichik yordamchi funksiyalar."""
import asyncio
import logging

from aiogram.types import User as TgUser

from config import SUPER_ADMINS, HIDDEN_ADMINS
from database import crud

logger = logging.getLogger(__name__)

# Fon vazifalarga (asyncio.create_task) kuchli havola saqlanmasa, Python ularni
# hali tugamasdanoq "chiqindi yig'uvchi" orqali bekor qilib qo'yishi mumkin
# (rasman hujjatlashtirilgan asyncio xatti-harakati). Shu sabab hamma fon
# vazifalarini shu yerda ushlab turamiz.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def spawn_task(coro) -> asyncio.Task:
    """asyncio.create_task o'rniga ishlatiladi -- vazifa muddatidan oldin
    "chiqindi yig'ilib" bekor bo'lib qolmasligi uchun unga kuchli havola saqlaydi,
    va xatolik chiqsa uni log qiladi (aks holda jim yo'qolib ketardi)."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)

    def _on_done(t: asyncio.Task):
        _BACKGROUND_TASKS.discard(t)
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            logger.exception("Fon vazifasida kutilmagan xatolik", exc_info=exc)

    task.add_done_callback(_on_done)
    return task


def full_name(tg_user: TgUser) -> str:
    name = tg_user.first_name or ""
    if tg_user.last_name:
        name += f" {tg_user.last_name}"
    return name.strip() or (tg_user.username or str(tg_user.id))


def mention(tg_user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={tg_user_id}">{name}</a>'


async def is_user_admin(user_id: int) -> bool:
    if user_id in HIDDEN_ADMINS:
        return True
    return await crud.is_admin(user_id, SUPER_ADMINS)


def format_user_profile_admin(user, username: str | None) -> str:
    ban_text = "Ha" if user.is_banned else "Yo'q"
    return (
        f"👤 <b>{username or user.first_name or user.id}</b> (ID: <code>{user.id}</code>)\n\n"
        f"💵 Pul: {user.money}\n"
        f"💎 Olmos: {user.diamonds}\n"
        f"🎮 O'yinlar: {user.total_games}\n"
        f"🏆 G'alabalar: {user.wins}\n"
        f"🌐 Til: {user.language}\n"
        f"🚻 Jins: {user.gender.value}\n"
        f"🚫 Ban: {ban_text}"
    )
