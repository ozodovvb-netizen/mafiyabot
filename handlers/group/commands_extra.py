"""
Guruh uchun qo'shimcha buyruqlar:
  /start   - (guruhda) admin ro'yxatdan o'tishni majburiy yakunlab, o'yinni darhol boshlaydi
             (MIN_PLAYERS yetarli bo'lmasa ham)
  /leave   - o'yindan/ro'yxatdan chiqish
  /lang    - guruhning standart tilini o'zgartirish (faqat adminlar)
  /sozlamalar - guruh sozlamalarini ko'rish (faqat adminlar)
  /gsend, /give   - kimgadir reply qilib olmos hadya qilish (yoki "100-10" ko'rinishida - giveaway, faqat admin)
  /mgive          - kimgadir reply qilib pul hadya qilish (yoki "100-10" ko'rinishida - giveaway, faqat admin)
  /change         - /gsend bilan bir xil (olmos), giveaway rejimida ham ishlaydi
  /vsgame  - jamoaviy (versus) o'yin rejimi
"""
import logging
import asyncio
import random
import re

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MIN_PLAYERS
import config
from database import crud
from game.engine import ACTIVE_GAMES
from keyboards.common_kb import language_kb
from utils.helpers import spawn_task

router = Router(name="group_commands_extra")
logger = logging.getLogger(__name__)

GIVEAWAY_RE = re.compile(r"^(\d+)\s*-\s*(\d+)$")
# giveaway_id -> {chat_id, message_id, amount, count, diamonds, participants: {uid: name}}
ACTIVE_GIVEAWAYS: dict[str, dict] = {}
_giveaway_seq = 0


async def is_group_admin(message: Message) -> bool:
    """Guruh admini yoki bosh admin (SUPER_ADMINS/HIDDEN_ADMINS) ekanini tekshiradi."""
    if message.from_user.id in config.HIDDEN_ADMINS:
        return True
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
    if len(engine.players) < 2:
        await message.answer("❌ O'yinni boshlash uchun kamida 2 ta o'yinchi kerak.")
        return

    engine.registration_open = False
    await message.answer(f"▶️ Admin tomonidan o'yin majburiy boshlandi ({len(engine.players)} o'yinchi bilan).")
    spawn_task(_run_force_start(engine))


async def _run_force_start(engine):
    """start_game() ichida xatolik chiqsa ham, bu guruhda ko'rinadigan xabar bilan bildiradi
    (aks holda o'yin 'boshlandi' deyilib, lekin aslida hech narsa yuz bermay jim qolib ketardi)."""
    try:
        await engine.start_game(force=True)
    except Exception:
        logger.exception("Majburiy /start orqali o'yinni boshlashda xatolik (chat_id=%s)", engine.chat_id)
        ACTIVE_GAMES.pop(engine.chat_id, None)
        try:
            await engine.bot.send_message(
                engine.chat_id,
                "❌ O'yinni boshlashda kutilmagan xatolik yuz berdi. Iltimos, admin /admin orqali "
                "rollar to'g'ri sozlanganini tekshirsin, so'ng /game bilan qaytadan boshlang.",
            )
        except Exception:
            pass


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
    if (
        member.status not in ("administrator", "creator")
        and callback.from_user.id not in config.HIDDEN_ADMINS
        and not await crud.is_admin(callback.from_user.id, config.SUPER_ADMINS)
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


@router.message(Command("gsend", "give"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_gsend(message: Message, command: CommandObject):
    await _gift_or_giveaway(message, command, diamonds=True)


@router.message(Command("change"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_change(message: Message, command: CommandObject):
    await _gift_or_giveaway(message, command, diamonds=True)


@router.message(Command("mgive"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_mgive(message: Message, command: CommandObject):
    await _gift_or_giveaway(message, command, diamonds=False)


async def _gift_or_giveaway(message: Message, command: CommandObject, diamonds: bool):
    """Reply bo'lsa -- shaxsiy hadya (o'z hisobidan). Reply bo'lmasa va 'summa-son' formatida
    bo'lsa -- guruhga giveaway (faqat adminlar boshlaydi, bonus sifatida beriladi)."""
    args = (command.args or "").strip()
    m = GIVEAWAY_RE.match(args)
    if not message.reply_to_message and m:
        await _start_giveaway(message, int(m.group(1)), int(m.group(2)), diamonds)
        return
    await _gift_reply(message, command, diamonds)


async def _start_giveaway(message: Message, amount: int, count: int, diamonds: bool):
    global _giveaway_seq
    if not await is_group_admin(message):
        await message.answer("❌ Sovg'a (giveaway) tarqatishni faqat guruh adminlari boshlashi mumkin.")
        return
    if amount <= 0 or count <= 0:
        await message.answer("❌ Miqdor va odam sonini to'g'ri kiriting. Masalan: /mgive 100-10")
        return

    _giveaway_seq += 1
    gid = f"{message.chat.id}:{_giveaway_seq}"
    unit = "olmos" if diamonds else "$"
    ACTIVE_GIVEAWAYS[gid] = {
        "chat_id": message.chat.id, "amount": amount, "count": count,
        "diamonds": diamonds, "participants": {},
    }

    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Qatnashish (0)", callback_data=f"giveaway_join:{gid}")

    text = (
        f"{'💎' if diamonds else '💵'} <b>{message.from_user.full_name}</b> {count} ta odamga "
        f"{amount} {unit} tarqatyapti!\n\nQatnashish uchun pastdagi tugmani bosing."
    )
    msg = await message.answer(text, reply_markup=builder.as_markup())
    ACTIVE_GIVEAWAYS[gid]["message_id"] = msg.message_id
    spawn_task(_finish_giveaway(message.bot, gid))


async def _finish_giveaway(bot, gid: str, seconds: int = 30):
    await asyncio.sleep(seconds)
    data = ACTIVE_GIVEAWAYS.pop(gid, None)
    if not data:
        return
    unit = "olmos" if data["diamonds"] else "$"
    participants = list(data["participants"].items())  # [(uid, name), ...]

    if not participants:
        text = "🎁 Sovg'a tarqatish yakunlandi, lekin hech kim qatnashmadi."
    else:
        count = min(data["count"], len(participants))
        winners = random.sample(participants, count)
        share = data["amount"] // count
        for uid, _name in winners:
            if data["diamonds"]:
                await crud.update_user_balance(uid, diamond_delta=share)
            else:
                await crud.update_user_balance(uid, money_delta=share)
        names = ", ".join(name for _uid, name in winners)
        text = (
            f"🎉 <b>Sovg'a tarqatildi!</b>\nHar biriga: <b>{share} {unit}</b>\n\n🏆 G'oliblar:\n{names}"
        )
    try:
        await bot.edit_message_text(text, chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception:
        try:
            await bot.send_message(data["chat_id"], text)
        except Exception:
            pass


@router.callback_query(F.data.startswith("giveaway_join:"))
async def on_giveaway_join(callback: CallbackQuery):
    gid = callback.data.split(":", 1)[1]
    data = ACTIVE_GIVEAWAYS.get(gid)
    if not data:
        await callback.answer("⏰ Bu sovg'a tarqatish yakunlangan.", show_alert=True)
        return
    uid = callback.from_user.id
    if uid in data["participants"]:
        await callback.answer("ℹ️ Siz allaqachon qatnashyapsiz.")
        return
    data["participants"][uid] = callback.from_user.full_name
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🎁 Qatnashish ({len(data['participants'])})", callback_data=f"giveaway_join:{gid}"
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception:
        pass
    await callback.answer("✅ Qatnashdingiz!")


async def _gift_reply(message: Message, command: CommandObject, diamonds: bool):
    """Guruhda HAR QANDAY foydalanuvchi reply qilib o'z olmos/pulidan boshqasiga hadya qilishi mumkin."""
    cmd_name = "gsend" if diamonds else "mgive"
    unit = "olmos" if diamonds else "pul"
    if not message.reply_to_message:
        await message.answer(
            f"ℹ️ Kimgadir {unit} hadya qilish uchun o'sha odamning xabariga reply qilib, "
            f"masalan: <code>/{cmd_name} 10</code> deb yozing."
        )
        return
    try:
        amount = int((command.args or "").strip().split()[0])
        if amount <= 0:
            raise ValueError
    except (ValueError, IndexError):
        await message.answer(f"❌ Miqdorni to'g'ri kiriting. Masalan: /{cmd_name} 10")
        return

    sender_tg = message.from_user
    target_tg = message.reply_to_message.from_user
    if target_tg.id == sender_tg.id:
        await message.answer("❌ O'zingizga hadya bera olmaysiz.")
        return
    if target_tg.is_bot:
        await message.answer("❌ Botga hadya bera olmaysiz.")
        return

    sender, _ = await crud.get_or_create_user(sender_tg.id, sender_tg.username, sender_tg.full_name)
    balance = sender.diamonds if diamonds else sender.money
    if balance < amount:
        await message.answer(f"❌ Hisobingizda yetarli {unit} yo'q (balansingiz: {balance}).")
        return

    await crud.get_or_create_user(target_tg.id, target_tg.username, target_tg.full_name)
    if diamonds:
        await crud.update_user_balance(sender_tg.id, diamond_delta=-amount)
        await crud.update_user_balance(target_tg.id, diamond_delta=amount)
        emoji = "💎"
    else:
        await crud.update_user_balance(sender_tg.id, money_delta=-amount)
        await crud.update_user_balance(target_tg.id, money_delta=amount)
        emoji = "💵"

    await message.answer(
        f"{emoji} <b>{sender_tg.full_name}</b> — <b>{target_tg.full_name}</b>ga {amount} {unit} hadya qildi!"
    )


def _medal(i: int) -> str:
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, "⭐" if i < 9 else "👤")


@router.message(Command("boylar"))
async def cmd_boylar(message: Message):
    """💰 Eng boylar reytingi (dollar va olmos bo'yicha) - istalgan chatda ishlaydi."""
    top_money = await crud.get_top_users_by_money(5)
    top_diamonds = await crud.get_top_users_by_diamonds(5)

    def _line(u, value: int, unit: str, i: int) -> str:
        name = u.first_name or (f"@{u.username}" if u.username else str(u.id))
        tag = f" (@{u.username})" if u.username and u.first_name else ""
        return f"{_medal(i)} {name}{tag} — {value:,} {unit}".replace(",", " ")

    money_lines = "\n".join(_line(u, u.money, "💵", i) for i, u in enumerate(top_money)) or "—"
    diamond_lines = "\n".join(_line(u, u.diamonds, "💎", i) for i, u in enumerate(top_diamonds)) or "—"

    text = (
        "🏆 <b>Eng boylar (Dollar bo'yicha)</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"{money_lines}\n\n"
        "💎 <b>Eng boylar (Olmos bo'yicha)</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"{diamond_lines}"
    )
    await message.answer(text)


@router.message(Command("vsgame"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_vsgame(message: Message):
    # ESLATMA: alohida "jamoa-jamoaga" qoidalari (jamoalar qanday tuzilishi, maxsus g'alaba
    # sharti) hali loyihalashtirilmagan, shuning uchun hozircha /vsgame oddiy /game oqimini
    # ishga tushiradi (ilgari faqat "hali tayyor emas" deb yozib, hech narsa qilmasdi).
    from handlers.group.game_start import cmd_game
    await message.answer(
        "🆚 Jamoaviy (versus) rejimning maxsus qoidalari hali ishlab chiqilmoqda — "
        "hozircha oddiy o'yin sifatida boshlanadi."
    )
    await cmd_game(message)
