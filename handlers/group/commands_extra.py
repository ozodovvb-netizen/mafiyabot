"""
Guruh uchun qo'shimcha buyruqlar:
  /start   - (guruhda) admin ro'yxatdan o'tishni majburiy yakunlab, o'yinni darhol boshlaydi
             (MIN_PLAYERS yetarli bo'lmasa ham)
  /leave   - o'yindan/ro'yxatdan chiqish
  /lang    - guruhning standart tilini o'zgartirish (faqat adminlar)
  /sozlamalar - guruh sozlamalarini ko'rish (faqat adminlar)
  /gsend   - kimgadir reply qilib olmos berish (faqat adminlar)
  /mgive   - kimgadir reply qilib pul berish (faqat adminlar)
  /vsgame  - jamoaviy (versus) o'yin rejimi
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import MIN_PLAYERS
import config
from database import crud
from game.engine import ACTIVE_GAMES
from keyboards.common_kb import language_kb

router = Router(name="group_commands_extra")
logger = logging.getLogger(__name__)


async def is_group_admin(message: Message) -> bool:
    """Guruh admini yoki bosh admin (SUPER_ADMINS) ekanini tekshiradi."""
    if await crud.is_admin(message.from_user.id, config.SUPER_ADMINS):
        return True
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


@router.message(Command("start"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_force_start(message: Message):
    """Guruhda /start -- admin ro'yxatdan o'tishni yopib, o'yinni darhol boshlaydi."""
    engine = ACTIVE_GAMES.get(message.chat.id)
    if not engine:
        await message.answer("❌ Hozir bu guruhda faol ro'yxatdan o'tish yo'q. Avval /game yuboring.")
        return
    if not engine.registration_open:
        await message.answer("⚠️ O'yin allaqachon boshlangan.")
        return
    if not await is_group_admin(message):
        await message.answer("❌ Ro'yxatdan o'tishni muddatidan oldin faqat guruh admini boshlashi mumkin.")
        return
    if len(engine.players) < 3:
        await message.answer("❌ O'yinni boshlash uchun kamida 3 ta o'yinchi kerak.")
        return

    engine.registration_open = False
    await message.answer(f"▶️ Admin tomonidan o'yin majburiy boshlandi ({len(engine.players)} o'yinchi bilan).")
    await engine.start_game()


@router.message(Command("leave"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_leave(message: Message):
    engine = ACTIVE_GAMES.get(message.chat.id)
    if not engine:
        await message.answer("❌ Bu guruhda faol o'yin/ro'yxatdan o'tish yo'q.")
        return
    user_id = message.from_user.id
    if user_id not in engine.players:
        await message.answer("ℹ️ Siz bu o'yinga qo'shilmagansiz.")
        return
    if not engine.registration_open:
        await message.answer("❌ O'yin allaqachon boshlangan, endi chiqib bo'lmaydi.")
        return
    del engine.players[user_id]
    await message.answer(f"👋 {message.from_user.full_name} o'yindan chiqdi.")
    await engine.refresh_registration_message()


@router.message(Command("lang"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_group_lang(message: Message):
    if not await is_group_admin(message):
        await message.answer("❌ Bu buyruq faqat guruh adminlari uchun.")
        return
    await message.answer(
        "🌐 Guruh uchun standart tilni tanlang:", reply_markup=language_kb(prefix="glang")
    )


@router.callback_query(F.data.startswith("glang:"))
async def on_group_lang_chosen(callback):
    if callback.message.chat.type not in ("group", "supergroup"):
        return
    member = await callback.bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in ("administrator", "creator") and not await crud.is_admin(
        callback.from_user.id, config.SUPER_ADMINS
    ):
        await callback.answer("❌ Faqat adminlar uchun.", show_alert=True)
        return
    lang = callback.data.split(":", 1)[1]
    await crud.set_group_language(callback.message.chat.id, lang)
    engine = ACTIVE_GAMES.get(callback.message.chat.id)
    if engine:
        engine.lang = lang
    await callback.message.edit_text(f"✅ Guruh tili o'zgartirildi: {lang}")
    await callback.answer()


@router.message(Command("sozlamalar"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_group_settings(message: Message):
    if not await is_group_admin(message):
        await message.answer("❌ Bu buyruq faqat guruh adminlari uchun.")
        return
    lang = await crud.get_group_language(message.chat.id)
    engine = ACTIVE_GAMES.get(message.chat.id)
    status = "❌ Faol o'yin yo'q"
    if engine:
        status = "🟢 Ro'yxatdan o'tish davom etmoqda" if engine.registration_open else "🎮 O'yin ketmoqda"
    await message.answer(
        "⚙️ <b>Guruh sozlamalari</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"🌐 Til: {lang}\n"
        f"👥 Minimal o'yinchilar: {MIN_PLAYERS}\n"
        f"📊 Holat: {status}\n\n"
        "Tilni o'zgartirish uchun: /lang"
    )


@router.message(Command("gsend"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_gsend(message: Message, command: CommandObject):
    await _give_reply(message, command, diamonds=True)


@router.message(Command("mgive"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_mgive(message: Message, command: CommandObject):
    await _give_reply(message, command, diamonds=False)


async def _give_reply(message: Message, command: CommandObject, diamonds: bool):
    if not await is_group_admin(message):
        await message.answer("❌ Bu buyruq faqat guruh adminlari uchun.")
        return
    if not message.reply_to_message:
        unit = "olmos" if diamonds else "pul"
        await message.answer(f"ℹ️ Kimgadir {unit} berish uchun o'sha odamning xabariga reply qilib, "
                              f"masalan: <code>/{'gsend' if diamonds else 'mgive'} 10</code> deb yozing.")
        return
    try:
        amount = int((command.args or "").strip().split()[0])
        if amount <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("❌ Miqdorni to'g'ri kiriting. Masalan: /gsend 10")
        return

    target = message.reply_to_message.from_user
    await crud.get_or_create_user(target.id, target.username, target.full_name)
    if diamonds:
        await crud.update_user_balance(target.id, diamond_delta=amount)
        await message.answer(f"💎 {target.full_name}ga {amount} ta olmos berildi.")
    else:
        await crud.update_user_balance(target.id, money_delta=amount)
        await message.answer(f"💵 {target.full_name}ga {amount} pul berildi.")


@router.message(Command("vsgame"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_vsgame(message: Message):
    # ESLATMA: bu rejim (jamoaviy/versus o'yin) videoda ko'ringan, lekin uning to'liq ichki
    # qoidalarini (jamoalar qanday tuzilishi, g'alaba sharti) kadrlardan aniq o'qib bo'lmadi.
    # Hozircha oddiy /game rejimiga yo'naltiramiz -- keyingi bosqichda screenshotlar bilan
    # to'liq amalga oshiramiz.
    await message.answer(
        "🆚 Jamoaviy (versus) o'yin rejimi hali ishlab chiqilmoqda.\n"
        "Hozircha /game orqali oddiy o'yinni boshlashingiz mumkin."
    )
