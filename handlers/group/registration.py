"""
Guruh o'yini bilan bog'liq callbacklar va xabar tinglovchilari:
  - Tungi harakat tanlash (night_act:)
  - Kunduzgi ovoz berish (vote_like: / vote_dislike:)
  - Oxirgi so'z (endi guruhda emas — botning shaxsiy chatida yozilgan matnni GameEngine
    kutmoqda bo'lsa ushlab oladi, keyin guruhga e'lon qilinadi)
  - Faolsizlarni kuzatish (juda uzoq javob bermasa ogohlantirish/chetlatish)
  - Tunda guruh chatini bloklash (yozgan foydalanuvchi xabari o'chirilib, 1 daqiqaga mute qilinadi)
"""
import asyncio
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardBuilder

from game.engine import ACTIVE_GAMES
from locales.texts import t

router = Router(name="group_registration")

NIGHT_MUTE_SECONDS = 60

# user_id -> asyncio.Future - oxirgi so'zni kutayotgan "signal"
# (o'yinchi botning shaxsiy chatiga yozadi, guruhga emas)
LAST_WORDS_LISTENERS: dict[int, asyncio.Future] = {}


async def _is_night_chat_spam(message: Message) -> bool:
    """Faqat: guruh chatida, faol o'yin tunda, va matn buyruq (/...) bo'lmasa True."""
    if message.chat.type not in ("group", "supergroup"):
        return False
    if not message.from_user or message.from_user.is_bot:
        return False
    engine = ACTIVE_GAMES.get(message.chat.id)
    if not engine or engine.phase != "night":
        return False
    if message.text and message.text.startswith("/"):
        return False
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ("administrator", "creator"):
            return False
    except Exception:
        pass
    return True


@router.message(_is_night_chat_spam)
async def block_night_group_chat(message: Message):
    """Tun paytida guruhga yozilgan xabarlarni o'chirib, yozgan odamni 1 daqiqaga mute qiladi."""
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.utcnow() + timedelta(seconds=NIGHT_MUTE_SECONDS),
        )
    except Exception:
        pass  # bot cheklash huquqiga ega bo'lmasligi mumkin


@router.callback_query(F.data.startswith("night_act:"))
async def on_night_action(callback: CallbackQuery):
    _, chat_id_str, target_id_str = callback.data.split(":")
    chat_id, target_id = int(chat_id_str), int(target_id_str)
    engine = ACTIVE_GAMES.get(chat_id)
    if not engine:
        await callback.answer("❌ O'yin allaqachon tugagan.", show_alert=True)
        return
    await engine.register_night_action(callback.from_user.id, target_id)
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

    voter = engine.players.get(callback.from_user.id)
    target = engine.players.get(nominee_id)
    voter_name = voter.name if voter else callback.from_user.full_name
    target_name = target.name if target else "?"

    go_to_group_kb = InlineKeyboardBuilder()
    group_url = engine.group_link or f"https://t.me/c/{str(chat_id)[4:]}"
    go_to_group_kb.button(text="↩️ Guruhga o'tish", url=group_url)

    try:
        await callback.message.edit_text(
            f"✅ Siz {target_name}ga ovoz berdingiz.", reply_markup=go_to_group_kb.as_markup()
        )
    except Exception:
        pass

    try:
        from utils.helpers import mention
        await callback.bot.send_message(
            chat_id,
            t(
                "vote_recorded", engine.lang,
                voter=mention(callback.from_user.id, voter_name),
                target=mention(nominee_id, target_name),
            ),
        )
    except Exception:
        pass

    await callback.answer("✅ Ovoz qabul qilindi.")


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
    await engine.refresh_vote_counts()
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
    await engine.refresh_vote_counts()
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
