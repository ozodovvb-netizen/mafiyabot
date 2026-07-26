"""Turli joylarda ishlatiladigan kichik yordamchi funksiyalar."""
from aiogram.types import User as TgUser

from config import SUPER_ADMINS, HIDDEN_ADMINS
from database import crud


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
