"""
/start komandasi.

Oqim:
1. Foydalanuvchi birinchi marta kirsa -> til tanlash so'raladi.
2. Til tanlangach -> jins tanlash so'raladi.
3. Jins tanlangach -> asosiy start menyusi ko'rsatiladi.
4. Agar foydalanuvchi avval til/jins tanlagan bo'lsa -> to'g'ridan-to'g'ri asosiy menyu.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import MAX_PLAYERS
from database import crud
from database.models import GenderEnum
from locales.texts import t
from keyboards.common_kb import language_kb, gender_kb
from keyboards.user_kb import start_menu_kb
from utils.helpers import full_name, is_user_admin
from game.engine import ACTIVE_GAMES

router = Router(name="start")


async def send_start_menu(message_or_cb, lang: str, edit: bool = False):
    user_id = message_or_cb.from_user.id
    admin_username = await crud.get_setting("admin_username", "@Hackeruzbekistan001")
    text = t("start_welcome", lang, max_players=MAX_PLAYERS, admin_username=admin_username)
    kb = start_menu_kb(lang, is_admin=await is_user_admin(user_id), admin_username=admin_username)
    if edit:
        await message_or_cb.message.edit_text(text, reply_markup=kb)
    else:
        await message_or_cb.answer(text, reply_markup=kb)


async def handle_join_payload(message: Message, session_id: int, user, lang: str, user_id: int, display_name: str):
    """Foydalanuvchi guruhdagi 'Qo'shilish' tugmasi orqali botga kelganda ishlaydi."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    target_engine = None
    for engine in ACTIVE_GAMES.values():
        if engine.session_id == session_id:
            target_engine = engine
            break

    if not target_engine:
        await message.answer("❌ Bu o'yin uchun ro'yxatdan o'tish yopilgan yoki o'yin topilmadi.")
        return

    go_to_group_kb = None
    if target_engine.group_link:
        builder = InlineKeyboardBuilder()
        builder.button(text=t("btn_go_to_group", lang), url=target_engine.group_link)
        go_to_group_kb = builder.as_markup()

    if user_id in target_engine.players:
        await message.answer("ℹ️ Siz bu o'yinga allaqachon qo'shilgansiz.", reply_markup=go_to_group_kb)
        return

    if not target_engine.registration_open:
        await message.answer("⏰ Siz o'yinga kech qoldingiz. Ro'yxatdan o'tish allaqachon yopilgan.", reply_markup=go_to_group_kb)
        return

    added = target_engine.add_player(user_id, display_name)
    await crud.add_game_player(session_id, user_id, display_name)

    if not added:
        await message.answer("ℹ️ Siz bu o'yinga allaqachon qo'shilgansiz.", reply_markup=go_to_group_kb)
        return

    await message.answer(t("joined_game_success", lang), reply_markup=go_to_group_kb)

    # Guruhdagi ro'yxatni yangilash (agar registratsiya xabari mavjud bo'lsa)
    try:
        await target_engine.refresh_registration_message()
    except Exception:
        pass


@router.message(CommandStart(deep_link=True), F.chat.type == "private")
async def cmd_start_deeplink(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    user, created = await crud.get_or_create_user(tg_user.id, tg_user.username, full_name(tg_user))

    if not user.language:
        await state.update_data(pending_payload=command.args)
        await message.answer(t("choose_language", None), reply_markup=language_kb())
        return

    if user.gender == GenderEnum.unset:
        await state.update_data(pending_payload=command.args)
        await message.answer(t("choose_gender", user.language), reply_markup=gender_kb(user.language))
        return

    payload = command.args or ""
    if payload.startswith("join_"):
        session_id = int(payload.split("_", 1)[1])
        await handle_join_payload(message, session_id, user, user.language, tg_user.id, full_name(tg_user))
    else:
        await send_start_menu(message, user.language)


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    user, created = await crud.get_or_create_user(tg_user.id, tg_user.username, full_name(tg_user))

    if not user.language:
        await message.answer(t("choose_language", None), reply_markup=language_kb())
        return

    if user.gender == GenderEnum.unset:
        await message.answer(t("choose_gender", user.language), reply_markup=gender_kb(user.language))
        return

    await send_start_menu(message, user.language)


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    await crud.set_user_language(callback.from_user.id, lang)
    user = await crud.get_user(callback.from_user.id)

    await callback.message.edit_text(t("language_saved", lang))

    if user.gender == GenderEnum.unset:
        await callback.message.answer(t("choose_gender", lang), reply_markup=gender_kb(lang))
    else:
        await _continue_after_setup(callback.message, user, state)
    await callback.answer()


@router.callback_query(F.data.startswith("gender:"))
async def on_gender_chosen(callback: CallbackQuery, state: FSMContext):
    gender_str = callback.data.split(":", 1)[1]
    gender = GenderEnum.male if gender_str == "male" else GenderEnum.female
    await crud.set_user_gender(callback.from_user.id, gender)
    user = await crud.get_user(callback.from_user.id)

    await callback.message.delete()
    await _continue_after_setup(callback.message, user, state)
    await callback.answer()


async def _continue_after_setup(message: Message, user, state: FSMContext):
    """Til/jins tanlangach - agar guruhdan kelgan bo'lsa o'yinga qo'shadi, aks holda asosiy menyu."""
    data = await state.get_data()
    payload = data.get("pending_payload")
    await state.clear()
    if payload and payload.startswith("join_"):
        session_id = int(payload.split("_", 1)[1])
        await handle_join_payload(message, session_id, user, user.language, user.id, user.first_name or str(user.id))
    else:
        await send_start_menu(message, user.language)


@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await crud.get_user(callback.from_user.id)
    await send_start_menu(callback, user.language, edit=True)
    await callback.answer()


@router.callback_query(F.data == "open:questions")
async def open_questions(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    admin_username = await crud.get_setting("admin_username", "@Hackeruzbekistan001")
    await callback.answer(f"{admin_username}", show_alert=True)


@router.callback_query(F.data == "open:change_language")
async def open_change_language(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    await callback.message.edit_text(t("choose_language", user.language), reply_markup=language_kb())
    await callback.answer()
