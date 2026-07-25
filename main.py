"""
Botni ishga tushiruvchi asosiy fayl.

Ishga tushirish:
    python main.py

Talab qilinadi:
    - .env faylida BOT_TOKEN, DATABASE_URL, SUPER_ADMINS to'ldirilgan bo'lishi kerak
    - PostgreSQL ishga tushirilgan va DATABASE_URL to'g'ri ko'rsatilgan bo'lishi kerak
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from config import BOT_TOKEN, SUPER_ADMINS
from database.db import init_db

# --- Foydalanuvchi handlerlari ---
from handlers.user import start, profile, protections, shop, money, money_shop, diamonds, hero, premium_groups, roles_info

# --- Admin handlerlari ---
from handlers.admin import (
    panel, users_admin, shop_admin, heroes_admin, roles_admin,
    premium_groups_admin, prices_admin, diamond_requests_admin, settings_admin,
)

# --- Guruh (o'yin) handlerlari ---
from handlers.group import game_start, registration

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Admin routerlari (birinchi navbatda - "adm:" callbacklari ustuvor bo'lishi uchun)
    dp.include_router(panel.router)
    dp.include_router(users_admin.router)
    dp.include_router(shop_admin.router)
    dp.include_router(heroes_admin.router)
    dp.include_router(roles_admin.router)
    dp.include_router(premium_groups_admin.router)
    dp.include_router(prices_admin.router)
    dp.include_router(diamond_requests_admin.router)
    dp.include_router(settings_admin.router)

    # Guruh (o'yin) routerlari
    dp.include_router(game_start.router)
    dp.include_router(registration.router)

    # Foydalanuvchi (shaxsiy chat) routerlari
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(protections.router)
    dp.include_router(shop.router)
    dp.include_router(money.router)
    dp.include_router(money_shop.router)
    dp.include_router(diamonds.router)
    dp.include_router(hero.router)
    dp.include_router(premium_groups.router)
    dp.include_router(roles_info.router)

    await init_db()
    logging.info("Baza tayyor. Bot ishga tushmoqda...")

    # Haqiqiy bot username'ni Telegram'dan olamiz (.env dagi BOT_USERNAME noto'g'ri/eskirgan
    # bo'lsa ham "Guruhga qo'shish" va "O'yinga qo'shilish" tugmalari to'g'ri ishlashi uchun).
    me = await bot.get_me()
    if config.BOT_USERNAME != me.username:
        logging.warning(
            "BOT_USERNAME .env da '%s' deb yozilgan, lekin haqiqiy bot username '@%s'. "
            "Avtomatik to'g'irlandi, lekin .env dagi BOT_USERNAME ni ham yangilab qo'yish tavsiya etiladi.",
            config.BOT_USERNAME, me.username,
        )
    config.BOT_USERNAME = me.username
    logging.info("Bot: @%s (id=%s)", me.username, me.id)

    if not SUPER_ADMINS:
        logging.warning(
            "SUPER_ADMINS bo'sh! .env dagi SUPER_ADMINS qiymatini tekshiring "
            "(faqat raqamli Telegram ID, tirnoqsiz, vergul bilan ajratilgan). "
            "Bu bo'sh bo'lsa hech kim /admin panelga kira olmaydi."
        )
    else:
        logging.info("SUPER_ADMINS aniqlandi: %s", SUPER_ADMINS)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
