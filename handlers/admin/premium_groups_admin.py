"""Admin - Premium guruhlar bo'limi: davlat bo'yicha guruh qo'shish/o'chirish."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from keyboards.admin_kb import premium_groups_list_kb, back_admin_kb, language_pick_for_group_kb
from states.states import AdminPremiumGroup
from utils.helpers import is_user_admin

router = Router(name="premium_groups_admin")


@router.callback_query(F.data == "adm:premium_groups")
async def adm_pg_choose_country(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🌍 Qaysi davlat/til uchun premium guruhlar ro'yxatini ko'rmoqchisiz yoki qo'shmoqchisiz?",
        reply_markup=language_pick_for_group_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pg_country:"))
async def adm_pg_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    country = callback.data.split(":", 1)[1]
    await state.update_data(pg_country=country)
    groups = await crud.get_premium_groups(country, active_only=False)
    await callback.message.edit_text(
        f"💎 <b>{country.upper()}</b> uchun premium guruhlar:\n\n"
        "O'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:",
        reply_markup=premium_groups_list_kb(groups, back_cb="adm:premium_groups"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_pg:del:"))
async def adm_pg_delete(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    pg_id = int(callback.data.split(":")[-1])
    await crud.delete_premium_group(pg_id)
    data = await state.get_data()
    country = data.get("pg_country", "uz")
    groups = await crud.get_premium_groups(country, active_only=False)
    await callback.message.edit_reply_markup(
        reply_markup=premium_groups_list_kb(groups, back_cb="adm:premium_groups")
    )
    await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_pg:add")
async def adm_pg_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminPremiumGroup.waiting_name)
    await callback.message.edit_text("📝 Guruh nomini kiriting:", reply_markup=back_admin_kb("adm:premium_groups"))
    await callback.answer()


@router.message(AdminPremiumGroup.waiting_name)
async def adm_pg_name(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminPremiumGroup.waiting_link)
    await message.answer("🔗 Guruh linkini kiriting (masalan https://t.me/+xxxxx):")


@router.message(AdminPremiumGroup.waiting_link)
async def adm_pg_link(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(link=message.text.strip())
    await state.set_state(AdminPremiumGroup.waiting_rank)
    await message.answer("💎 Reyting/olmos qiymatini kiriting (katta son - tepada chiqadi):")


@router.message(AdminPremiumGroup.waiting_rank)
async def adm_pg_rank(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.")
        return

    data = await state.get_data()
    country = data.get("pg_country", "uz")
    await crud.create_premium_group(
        country_code=country,
        name=data["name"],
        link=data["link"],
        diamond_rank=int(message.text.strip()),
    )
    await state.clear()
    groups = await crud.get_premium_groups(country, active_only=False)
    await message.answer(
        "✅ Premium guruh qo'shildi!",
        reply_markup=premium_groups_list_kb(groups, back_cb="adm:premium_groups"),
    )
