"""
Admin - Umumiy sozlamalar:
  - O'yin g'olib/yutqazgan mukofot miqdorlari
  - "Savollar uchun" tugmasidagi admin username
  - Olmos to'lovi uchun karta raqami
  - Adminlar ro'yxatini boshqarish (qo'shish/o'chirish)
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import SUPER_ADMINS
from database import crud
from keyboards.admin_kb import back_admin_kb
from states.states import AdminRewardSettings, AdminAdminUsername, AdminCardNumber, AdminAddAdmin
from utils.helpers import is_user_admin

router = Router(name="settings_admin")


# --- Mukofot sozlamalari ---
@router.callback_query(F.data == "adm:rewards")
async def adm_rewards_show(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    r = await crud.get_reward_settings()
    text = (
        "🏆 <b>Mukofot sozlamalari</b>\n\n"
        f"🥇 G'olib: {r.winner_money} 💵 / {r.winner_diamond} 💎\n"
        f"🥈 Yutqazgan: {r.loser_money} 💵 / {r.loser_diamond} 💎\n\n"
        "O'zgartirish uchun yangi qiymatlarni tartib bilan yuboring."
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ O'zgartirish", callback_data="adm_rewards:edit")
    builder.button(text="↩️ Orqaga", callback_data="adm:main")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "adm_rewards:edit")
async def adm_rewards_edit_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminRewardSettings.waiting_winner_money)
    await callback.message.edit_text("🥇 G'olibga necha Dollar berilsin?", reply_markup=back_admin_kb("adm:rewards"))
    await callback.answer()


@router.message(AdminRewardSettings.waiting_winner_money)
async def adm_rewards_winner_money(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:rewards"))
        return
    await state.update_data(winner_money=int(message.text.strip()))
    await state.set_state(AdminRewardSettings.waiting_winner_diamond)
    await message.answer("🥇 G'olibga necha Olmos berilsin?", reply_markup=back_admin_kb("adm:rewards"))


@router.message(AdminRewardSettings.waiting_winner_diamond)
async def adm_rewards_winner_diamond(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:rewards"))
        return
    await state.update_data(winner_diamond=int(message.text.strip()))
    await state.set_state(AdminRewardSettings.waiting_loser_money)
    await message.answer("🥈 Yutqazganga necha Dollar berilsin?", reply_markup=back_admin_kb("adm:rewards"))


@router.message(AdminRewardSettings.waiting_loser_money)
async def adm_rewards_loser_money(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:rewards"))
        return
    await state.update_data(loser_money=int(message.text.strip()))
    await state.set_state(AdminRewardSettings.waiting_loser_diamond)
    await message.answer("🥈 Yutqazganga necha Olmos berilsin?", reply_markup=back_admin_kb("adm:rewards"))


@router.message(AdminRewardSettings.waiting_loser_diamond)
async def adm_rewards_loser_diamond(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:rewards"))
        return
    data = await state.get_data()
    await crud.update_reward_settings(
        winner_money=data["winner_money"],
        winner_diamond=data["winner_diamond"],
        loser_money=data["loser_money"],
        loser_diamond=int(message.text.strip()),
    )
    await state.clear()
    await message.answer("✅ Mukofot sozlamalari yangilandi!", reply_markup=back_admin_kb())


# --- Admin username (Savollar uchun) ---
@router.callback_query(F.data == "adm:admin_username")
async def adm_username_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    current = await crud.get_setting("admin_username", "@Hackeruzbekistan001")
    await state.set_state(AdminAdminUsername.waiting_username)
    await callback.message.edit_text(
        f"👤 Hozirgi admin username: {current}\n\nYangi username yuboring (masalan @username):",
        reply_markup=back_admin_kb(),
    )
    await callback.answer()


@router.message(AdminAdminUsername.waiting_username)
async def adm_username_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await crud.set_setting("admin_username", message.text.strip())
    await state.clear()
    await message.answer("✅ Admin username yangilandi!", reply_markup=back_admin_kb())


# --- Karta raqami (olmos to'lovi uchun) ---
@router.callback_query(F.data == "adm:card_number")
async def adm_card_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    current = await crud.get_setting("payment_card_number", "kiritilmagan")
    await state.set_state(AdminCardNumber.waiting_card)
    await callback.message.edit_text(
        f"💳 Hozirgi karta raqami: {current}\n\nYangi karta raqamini yuboring:",
        reply_markup=back_admin_kb(),
    )
    await callback.answer()


@router.message(AdminCardNumber.waiting_card)
async def adm_card_save(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await crud.set_setting("payment_card_number", message.text.strip())
    await state.clear()
    await message.answer("✅ Karta raqami yangilandi!", reply_markup=back_admin_kb())


# --- Adminlar ro'yxati ---
@router.callback_query(F.data == "adm:admins")
async def adm_admins_list(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in SUPER_ADMINS:
        await callback.answer("❌ Faqat bosh admin buni ko'ra oladi.", show_alert=True)
        return
    await state.clear()

    from database.db import async_session
    from sqlalchemy import select
    from database.models import AdminUser

    async with async_session() as s:
        res = await s.execute(select(AdminUser))
        admins = list(res.scalars().all())

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for a in admins:
        builder.button(text=f"🗑 {a.user_id}", callback_data=f"adm_admin:del:{a.user_id}")
    builder.button(text="➕ Admin qo'shish", callback_data="adm_admin:add")
    builder.button(text="↩️ Orqaga", callback_data="adm:main")
    builder.adjust(1)

    text = "👮 <b>Adminlar</b>\n\n" + "\n".join(f"• {a.user_id}" for a in admins) if admins else "👮 <b>Adminlar</b>\n\nHozircha qo'shimcha admin yo'q."
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("adm_admin:del:"))
async def adm_admin_delete(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in SUPER_ADMINS:
        await callback.answer()
        return
    admin_id = int(callback.data.split(":")[-1])
    await crud.remove_admin(admin_id)
    await callback.answer("🗑 Admin olib tashlandi")
    await adm_admins_list(callback, state)


@router.callback_query(F.data == "adm_admin:add")
async def adm_admin_add_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in SUPER_ADMINS:
        await callback.answer()
        return
    await state.set_state(AdminAddAdmin.waiting_user_id)
    await callback.message.edit_text("🆔 Yangi adminning Telegram ID sini yuboring:", reply_markup=back_admin_kb())
    await callback.answer()


@router.message(AdminAddAdmin.waiting_user_id)
async def adm_admin_add_save(message: Message, state: FSMContext):
    # MUHIM: bu ADMIN QO'SHISH funksiyasi - faqat bosh admin (SUPER_ADMINS) bajara oladi,
    # oddiy is_user_admin (DB'dagi har qanday admin) yetarli emas.
    if message.from_user.id not in SUPER_ADMINS:
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (ID) yuboring.", reply_markup=back_admin_kb())
        return
    await crud.add_admin(int(message.text.strip()), added_by=message.from_user.id)
    await state.clear()
    await message.answer("✅ Yangi admin qo'shildi!", reply_markup=back_admin_kb())
