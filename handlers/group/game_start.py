"""
Guruhda o'yinni boshlash: /game komandasi.

Oqim:
  1. Guruhda /game yuborilsa - ro'yxatdan o'tish xabari chiqadi (deep-link tugma bilan).
  2. Foydalanuvchi tugmani bosib botga o'tadi -> /start join_<session_id> orqali ro'yxatdan o'tadi.
  3. REGISTRATION_SECONDS o'tgach (yoki admin /startgame desa) - agar yetarli o'yinchi bo'lsa, o'yin boshlanadi.
"""
import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from config import REGISTRATION_SECONDS, MIN_PLAYERS
from database import crud
from game.engine import GameEngine, ACTIVE_GAMES

router = Router(name="group_game_start")
logger = logging.getLogger(__name__)


@router.message(Command("game"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_game(message: Message):
    try:
        existing = ACTIVE_GAMES.get(message.chat.id)
        if existing:
            if not existing.registration_open:
                await message.answer("⚠️ Bu guruhda allaqachon o'yin ketmoqda.")
                return
            # Ro'yxatdan o'tish hali davom etmoqda -> xabarni qayta yuborib, qadaymiz
            # (qo'shilgan o'yinchilar ro'yxati tegilmaydi)
            await _send_and_pin_registration(existing, message)
            return

        session = await crud.create_game_session(message.chat.id, message.from_user.id)
        engine = GameEngine(message.bot, message.chat.id, session.id, message.from_user.id)
        engine.group_link = await _resolve_group_link(message)
        ACTIVE_GAMES[message.chat.id] = engine

        # ESLATMA: o'yinni boshlagan odam endi AVTOMATIK qo'shilmaydi -- xohlasa
        # o'zi ham hammasi kabi "Qo'shilish" tugmasini bosishi kerak.
        await _send_and_pin_registration(engine, message, banner=True)
        asyncio.create_task(registration_timer(engine))
    except Exception:
        logger.exception("/game buyrug'ida xatolik yuz berdi (chat_id=%s)", message.chat.id)
        ACTIVE_GAMES.pop(message.chat.id, None)
        await message.answer(
            "❌ O'yinni boshlashda xatolik yuz berdi. Admin /admin orqali rollar sozlanganini "
            "tekshirsin, keyin qayta urinib ko'ring."
        )


async def _resolve_group_link(message: Message) -> str | None:
    """'Guruhga o'tish' tugmasi ishlashi uchun haqiqiy havolani aniqlaydi.

    t.me/c/<id> formati ko'p holatda ishlamaydi (faqat allaqachon a'zo bo'lgan
    va Telegram ilovasida ochilgan holatlarda ishlaydi), shuning uchun:
      1) Guruh public bo'lsa (@username bor) -> https://t.me/<username>
      2) Aks holda bot orqali chaqiriladigan (yoki mavjud) invite link ishlatiladi
         (bot uchun "Foydalanuvchi qo'shish" admin huquqi kerak).
    """
    if message.chat.username:
        return f"https://t.me/{message.chat.username}"
    try:
        return await message.bot.export_chat_invite_link(message.chat.id)
    except Exception:
        logger.warning(
            "Guruh (chat_id=%s) uchun invite link olib bo'lmadi -- botga "
            "'Foydalanuvchilarni taklif qilish' admin huquqini bering.",
            message.chat.id,
        )
        return None


async def _send_and_pin_registration(engine: GameEngine, message: Message, banner: bool = False):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎮 Qo'shilish",
        url=f"https://t.me/{config.BOT_USERNAME}?start=join_{engine.session_id}",
    )
    text = await engine.registration_welcome_text() if banner else await engine.registration_message_text()
    msg = await message.answer(text, reply_markup=builder.as_markup())

    # Avvalgi ro'yxatdan o'tish xabarini yechib, yangisini qadaymiz
    if engine.registration_message_id:
        try:
            await message.bot.unpin_message(message.chat.id, engine.registration_message_id)
        except Exception:
            pass
    engine.registration_message_id = msg.message_id
    try:
        await message.bot.pin_chat_message(message.chat.id, msg.message_id, disable_notification=True)
    except Exception:
        pass  # bot admin bo'lmasa qadab bo'lmaydi -- o'yin baribir davom etadi


async def registration_timer(engine: GameEngine):
    await asyncio.sleep(REGISTRATION_SECONDS)
    if engine.chat_id not in ACTIVE_GAMES:
        return  # bekor qilingan yoki allaqachon boshlangan
    if not engine.registration_open:
        return  # admin /start orqali allaqachon majburiy boshlagan
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
    engine.stopped = True
    ACTIVE_GAMES.pop(message.chat.id, None)
    await message.answer("🛑 O'yin to'xtatildi.")
