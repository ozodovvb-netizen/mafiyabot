"""Admin - foydalanuvchini ID orqali topish, pul/olmos qo'shish-ayirish, ban."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from keyboards.admin_kb import user_management_kb, back_admin_kb
from states.states import AdminUserSearch
from utils.helpers import is_user_admin, format_user_profile_admin

router = Router(name="users_admin")


@router.callback_query(F.data == "adm:search_user")
async def start_search_user(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminUserSearch.waiting_user_id)
    await callback.message.edit_text(
        "🔍 Foydalanuvchining Telegram ID raqamini yuboring:", reply_markup=back_admin_kb()
    )
    await callback.answer()


@router.message(AdminUserSearch.waiting_user_id)
async def search_user_by_id(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat raqam (ID) yuboring.")
        return

    user_id = int(message.text.strip())
    user = await crud.get_user(user_id)
    await state.clear()

    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.", reply_markup=back_admin_kb())
        return

    await message.answer(
        format_user_profile_admin(user, user.username),
        reply_markup=user_management_kb(user_id),
    )


@router.callback_query(F.data.startswith("adm:user_money_add:"))
async def ask_money_add(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(AdminUserSearch.waiting_money_amount)
    await state.update_data(target_user_id=user_id, op="add")
    await callback.message.answer(f"➕ {user_id} ga qancha pul qo'shamiz? Raqam yuboring:")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:user_money_sub:"))
async def ask_money_sub(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(AdminUserSearch.waiting_money_amount)
    await state.update_data(target_user_id=user_id, op="sub")
    await callback.message.answer(f"➖ {user_id} dan qancha pul ayiramiz? Raqam yuboring:")
    await callback.answer()


@router.message(AdminUserSearch.waiting_money_amount)
async def apply_money_change(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    data = await state.get_data()
    amount = int(message.text.strip())
    if data["op"] == "sub":
        amount = -amount
    await crud.update_user_balance(data["target_user_id"], money_delta=amount)
    await state.clear()
    user = await crud.get_user(data["target_user_id"])
    await message.answer(
        f"✅ Yangilandi. Yangi balans: {user.money} 💵",
        reply_markup=user_management_kb(data["target_user_id"]),
    )


@router.callback_query(F.data.startswith("adm:user_diamond_add:"))
async def ask_diamond_add(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(AdminUserSearch.waiting_diamond_amount)
    await state.update_data(target_user_id=user_id, op="add")
    await callback.message.answer(f"➕ {user_id} ga qancha olmos qo'shamiz? Raqam yuboring:")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:user_diamond_sub:"))
async def ask_diamond_sub(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(AdminUserSearch.waiting_diamond_amount)
    await state.update_data(target_user_id=user_id, op="sub")
    await callback.message.answer(f"➖ {user_id} dan qancha olmos ayiramiz? Raqam yuboring:")
    await callback.answer()


@router.message(AdminUserSearch.waiting_diamond_amount)
async def apply_diamond_change(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return
    data = await state.get_data()
    amount = int(message.text.strip())
    if data["op"] == "sub":
        amount = -amount
    await crud.update_user_balance(data["target_user_id"], diamond_delta=amount)
    await state.clear()
    user = await crud.get_user(data["target_user_id"])
    await message.answer(
        f"✅ Yangilandi. Yangi balans: {user.diamonds} 💎",
        reply_markup=user_management_kb(data["target_user_id"]),
    )


@router.callback_query(F.data.startswith("adm:user_ban:"))
async def toggle_ban(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[-1])
    user = await crud.get_user(user_id)
    from database.db import async_session
    async with async_session() as s:
        u = await s.get(type(user), user_id)
        u.is_banned = not u.is_banned
        await s.commit()
    user = await crud.get_user(user_id)
    await callback.answer("🚫 Ban qilindi" if user.is_banned else "✅ Ban olib tashlandi", show_alert=True)
    await callback.message.edit_text(
        format_user_profile_admin(user, user.username), reply_markup=user_management_kb(user_id)
    )
