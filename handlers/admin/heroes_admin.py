"""Admin - Geroylar bo'limi: geroy qo'shish/o'chirish."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from keyboards.admin_kb import list_with_delete_kb, back_admin_kb
from states.states import AdminHero
from utils.helpers import is_user_admin

router = Router(name="heroes_admin")


@router.callback_query(F.data == "adm:heroes")
async def adm_heroes_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    heroes = await crud.get_heroes(active_only=False)
    await callback.message.edit_text(
        "🦸 <b>Geroylar</b>\n\nO'chirish uchun bosing, yangi qo'shish uchun pastdagi tugma:",
        reply_markup=list_with_delete_kb(heroes, "adm_hero"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_hero:del:"))
async def adm_hero_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    hero_id = int(callback.data.split(":")[-1])
    status = await crud.delete_hero(hero_id)
    heroes = await crud.get_heroes(active_only=False)
    await callback.message.edit_reply_markup(reply_markup=list_with_delete_kb(heroes, "adm_hero"))
    if status == "deactivated":
        await callback.answer("⚠️ Bu geroyni sotib olganlar bor, shuning uchun butunlay o'chirilmadi - nofaol qilindi (endi hech kimga ko'rinmaydi)", show_alert=True)
    else:
        await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_hero:add")
async def adm_hero_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminHero.waiting_name)
    await callback.message.edit_text("📝 Geroy nomini kiriting:", reply_markup=back_admin_kb("adm:heroes"))
    await callback.answer()


@router.message(AdminHero.waiting_name)
async def adm_hero_name(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminHero.waiting_abilities)
    await message.answer(
        "💪 Geroy o'yin davomida nimalar qila olishini yozing:",
        reply_markup=back_admin_kb("adm:heroes"),
    )


@router.message(AdminHero.waiting_abilities)
async def adm_hero_abilities(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(abilities_text=message.text.strip())
    await state.set_state(AdminHero.waiting_protection_text)
    await message.answer(
        "🛡 Geroy nimalardan himoya qila olishini yozing:",
        reply_markup=back_admin_kb("adm:heroes"),
    )


@router.message(AdminHero.waiting_protection_text)
async def adm_hero_protection(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    await state.update_data(protection_text=message.text.strip())
    await state.set_state(AdminHero.waiting_price_diamond)
    await message.answer(
        "💎 Narxini Olmosda kiriting:",
        reply_markup=back_admin_kb("adm:heroes"),
    )


@router.message(AdminHero.waiting_price_diamond)
async def adm_hero_price_diamond(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:heroes"))
        return
    await state.update_data(price_diamond=int(message.text.strip()))
    await state.set_state(AdminHero.waiting_price_stars)
    await message.answer(
        "⭐ Narxini Telegram Stars da kiriting:",
        reply_markup=back_admin_kb("adm:heroes"),
    )


@router.message(AdminHero.waiting_price_stars)
async def adm_hero_price_stars(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:heroes"))
        return
    data = await state.get_data()
    await crud.create_hero(
        name=data["name"],
        abilities_text=data["abilities_text"],
        protection_text=data["protection_text"],
        price_diamond=data["price_diamond"],
        price_stars=int(message.text.strip()),
    )
    await state.clear()
    heroes = await crud.get_heroes(active_only=False)
    await message.answer("✅ Geroy qo'shildi!", reply_markup=list_with_delete_kb(heroes, "adm_hero"))
