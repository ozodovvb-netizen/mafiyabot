"""
Admin - O'yin rejimlari bo'limi.

Har bir rejim (masalan "classic", "zombi", "chaos") o'zining o'yinchilar soni oralig'iga
ega: o'yin boshlanganda, joriy o'yinchilar soniga qarab mos rejim avtomatik tanlanadi va
faqat o'sha rejimga tegishli qilib belgilangan rollar ishlatiladi (rollarga rejim
"Rollar" bo'limida rol qo'shishda beriladi).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import crud
from keyboards.admin_kb import back_admin_kb
from states.states import AdminGameMode
from utils.helpers import is_user_admin

router = Router(name="game_modes_admin")


@router.callback_query(F.data == "adm:game_modes")
async def adm_modes_list(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    modes = await crud.get_game_modes(active_only=False)

    builder = InlineKeyboardBuilder()
    for m in modes:
        builder.button(
            text=f"🗑 {m.name} ({m.min_players}-{m.max_players})",
            callback_data=f"adm_mode:del:{m.id}",
        )
    builder.button(text="➕ Rejim qo'shish", callback_data="adm_mode:add")
    builder.button(text="↩️ Orqaga", callback_data="adm:main")
    builder.adjust(1)

    text = (
        "🎲 <b>O'yin rejimlari</b>\n\n"
        "O'yin boshlanganda o'yinchilar soniga qarab shu rejimlardan biri avtomatik "
        "tanlanadi va faqat o'sha rejimga tegishli rollar ishlatiladi "
        "('Rollar' bo'limida rol qo'shganda rejim tanlanadi).\n\n"
        "Hech qanday oraliqqa to'g'ri kelmasa - \"classic\" rejimi ishlatiladi.\n\n"
        + ("\n".join(f"• <b>{m.name}</b>: {m.min_players}-{m.max_players} kishi" for m in modes) or "— hozircha rejim yo'q —")
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("adm_mode:del:"))
async def adm_mode_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    mode_id = int(callback.data.split(":")[-1])
    await crud.delete_game_mode(mode_id)
    await callback.answer("🗑 O'chirildi")
    await adm_modes_list(callback)


@router.callback_query(F.data == "adm_mode:add")
async def adm_mode_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminGameMode.waiting_name)
    await callback.message.edit_text(
        "📝 Yangi rejim nomini kiriting (masalan: classic, zombi, chaos):",
        reply_markup=back_admin_kb("adm:game_modes"),
    )
    await callback.answer()


@router.message(AdminGameMode.waiting_name)
async def adm_mode_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip().lower())
    await state.set_state(AdminGameMode.waiting_min_players)
    await message.answer("👥 Bu rejim uchun eng kam o'yinchi soni nechta?")


@router.message(AdminGameMode.waiting_min_players)
async def adm_mode_min(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    await state.update_data(min_players=int(message.text.strip()))
    await state.set_state(AdminGameMode.waiting_max_players)
    await message.answer("👥 Bu rejim uchun eng ko'p o'yinchi soni nechta?")


@router.message(AdminGameMode.waiting_max_players)
async def adm_mode_max(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    data = await state.get_data()
    await crud.create_game_mode(
        name=data["name"],
        min_players=data["min_players"],
        max_players=int(message.text.strip()),
    )
    await state.clear()
    await message.answer("✅ Rejim qo'shildi! Endi 'Rollar' bo'limida rol qo'shganda bu rejimni tanlashingiz mumkin.", reply_markup=back_admin_kb())
