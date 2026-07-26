"""
Guruh o'yini bilan bog'liq callbacklar va xabar tinglovchilari:
  - Tungi harakat tanlash (night_act:)
  - Kunduzgi ovoz berish (vote_like: / vote_dislike:)
  - Oxirgi so'z (endi guruhda emas — botning shaxsiy chatida yozilgan matnni GameEngine
    kutmoqda bo'lsa ushlab oladi, keyin guruhga e'lon qilinadi)
  - Faolsizlarni kuzatish (juda uzoq javob bermasa ogohlantirish/chetlatish)
"""
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from game.engine import ACTIVE_GAMES
from locales.texts import t

router = Router(name="group_registration")

# user_id -> asyncio.Future - oxirgi so'zni kutayotgan "signal"
# (o'yinchi botning shaxsiy chatiga yozadi, guruhga emas)
LAST_WORDS_LISTENERS: dict[int, asyncio.Future] = {}


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


@router.callback_query(F.data.startswith("nominate:"))
async def on_nominate(callback: CallbackQuery):
    _, chat_id_str, nominee_id_str = callback.data.split(":")
    chat_id, nominee_id = int(chat_id_str), int(nominee_id_str)
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer()
        return
    ok = engine.register_nomination(callback.from_user.id, nominee_id)
    if not ok:
        await callback.answer("❌ Ovoz berish yopilgan yoki siz tirik emassiz.", show_alert=True)
        return
    await callback.answer("✅ Nomzod tanlandi.")


@router.callback_query(F.data.startswith("vote_like:"))
async def on_vote_like(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer()
        return
    if not engine.register_vote(callback.from_user.id, "like"):
        await callback.answer("❌ Faqat tirik o'yinchilar ovoz bera oladi.", show_alert=True)
        return
    await callback.answer("👍")


@router.callback_query(F.data.startswith("vote_dislike:"))
async def on_vote_dislike(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer()
        return
    if not engine.register_vote(callback.from_user.id, "dislike"):
        await callback.answer("❌ Faqat tirik o'yinchilar ovoz bera oladi.", show_alert=True)
        return
    await callback.answer("👎")


def _awaiting_last_words(message: Message) -> bool:
    """Faqat GameEngine shu foydalanuvchidan aniq oxirgi so'z kutayotgan bo'lsagina True.
    Aks holda False qaytarib, boshqa handlerlarga (/start, FSM holatlari va h.k.) yo'l beramiz."""
    return message.from_user is not None and message.from_user.id in LAST_WORDS_LISTENERS


@router.message(F.chat.type == "private", _awaiting_last_words)
async def catch_last_words(message: Message):
    """GameEngine shu foydalanuvchidan (shaxsiy chatda) oxirgi so'z kutayotgan bo'lsa, ushlab oladi."""
    future = LAST_WORDS_LISTENERS.get(message.from_user.id)
    if future and not future.done():
        future.set_result(message.text or "...")
