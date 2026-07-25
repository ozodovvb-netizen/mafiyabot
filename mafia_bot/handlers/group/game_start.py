"""
Guruhda o'yinni boshlash: /game komandasi.

Oqim:
  1. Guruhda /game yuborilsa - ro'yxatdan o'tish xabari chiqadi (deep-link tugma bilan).
  2. Foydalanuvchi tugmani bosib botga o'tadi -> /start join_<session_id> orqali ro'yxatdan o'tadi.
  3. REGISTRATION_SECONDS o'tgach (yoki admin /startgame desa) - agar yetarli o'yinchi bo'lsa, o'yin boshlanadi.
"""
import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME, REGISTRATION_SECONDS, MIN_PLAYERS
from database import crud
from game.engine import GameEngine, ACTIVE_GAMES

router = Router(name="group_game_start")


@router.message(Command("game"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_game(message: Message):
    if message.chat.id in ACTIVE_GAMES:
        await message.answer("⚠️ Bu guruhda allaqachon o'yin ketmoqda yoki ro'yxatdan o'tish davom etmoqda.")
        return

    session = await crud.create_game_session(message.chat.id, message.from_user.id)
    engine = GameEngine(message.bot, message.chat.id, session.id, message.from_user.id)
    ACTIVE_GAMES[message.chat.id] = engine

    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎮 Qo'shilish",
        url=f"https://t.me/{BOT_USERNAME}?start=join_{session.id}",
    )
    text = await engine.registration_message_text()
    msg = await message.answer(text, reply_markup=builder.as_markup())

    asyncio.create_task(registration_timer(engine, msg))


async def registration_timer(engine: GameEngine, reg_message: Message):
    await asyncio.sleep(REGISTRATION_SECONDS)
    if engine.chat_id not in ACTIVE_GAMES:
        return  # bekor qilingan yoki allaqachon boshlangan
    engine.registration_open = False
    if len(engine.players) < MIN_PLAYERS:
        await engine.bot.send_message(
            engine.chat_id,
            f"❌ Yetarli o'yinchi yig'ilmadi ({len(engine.players)}/{MIN_PLAYERS}). O'yin bekor qilindi.",
        )
        ACTIVE_GAMES.pop(engine.chat_id, None)
        return
    await engine.start_game()


@router.message(Command("stop"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_stop_game(message: Message):
    engine = ACTIVE_GAMES.get(message.chat.id)
    if not engine:
        await message.answer("❌ Bu guruhda faol o'yin yo'q.")
        return
    if message.from_user.id != engine.host_id:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ("administrator", "creator"):
            await message.answer("❌ Faqat o'yinni boshlagan yoki guruh admini o'yinni to'xtata oladi.")
            return
    ACTIVE_GAMES.pop(message.chat.id, None)
    await message.answer("🛑 O'yin to'xtatildi.")
