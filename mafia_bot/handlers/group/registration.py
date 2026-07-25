"""
Guruh o'yini bilan bog'liq callbacklar va xabar tinglovchilari:
  - Tungi harakat tanlash (night_act:)
  - Kunduzgi ovoz berish (vote_like: / vote_dislike:)
  - Oxirgi so'z (guruh ichida yozilgan matnni GameEngine kutmoqda bo'lsa ushlab oladi)
  - Faolsizlarni kuzatish (juda uzoq javob bermasa ogohlantirish/chetlatish)
"""
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from game.engine import ACTIVE_GAMES
from locales.texts import t

router = Router(name="group_registration")

# (chat_id, user_id) -> asyncio.Future - oxirgi so'zni kutayotgan "signal"
LAST_WORDS_LISTENERS: dict[tuple[int, int], asyncio.Future] = {}


@router.callback_query(F.data.startswith("night_act:"))
async def on_night_action(callback: CallbackQuery):
    _, chat_id_str, target_id_str = callback.data.split(":")
    chat_id, target_id = int(chat_id_str), int(target_id_str)
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer("❌ O'yin allaqachon tugagan.", show_alert=True)
        return
    engine.register_night_action(callback.from_user.id, target_id)
    await callback.message.edit_text("✅ Tanlovingiz qabul qilindi.")
    await callback.answer()


@router.callback_query(F.data.startswith("vote_like:"))
async def on_vote_like(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer()
        return
    engine.register_vote(callback.from_user.id, "like")
    await callback.answer("👍")


@router.callback_query(F.data.startswith("vote_dislike:"))
async def on_vote_dislike(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer()
        return
    engine.register_vote(callback.from_user.id, "dislike")
    await callback.answer("👎")


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def catch_last_words(message: Message):
    """Agar GameEngine shu foydalanuvchidan oxirgi so'z kutayotgan bo'lsa, ushlab oladi."""
    key = (message.chat.id, message.from_user.id)
    future = LAST_WORDS_LISTENERS.get(key)
    if future and not future.done():
        future.set_result(message.text or "...")
