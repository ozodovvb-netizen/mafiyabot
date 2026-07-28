"""Admin - Pul (Dollar) va Olmos paketlari narxlarini boshqarish."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import crud
from keyboards.admin_kb import list_with_delete_kb, back_admin_kb
from states.states import AdminMoneyPackage, AdminDiamondPackage
from utils.helpers import is_user_admin

router = Router(name="prices_admin")


# --- Pul (Dollar) paketlari (Olmos evaziga Dollar sotib olish narxlari) ---
@router.callback_query(F.data == "adm:money_prices")
async def adm_money_prices_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    packages = await crud.get_money_packages(active_only=False)
    await callback.message.edit_text(
        "💵 <b>Pul (Dollar) paketlari</b>\n\nOlmos evaziga qancha Dollar berilishini sozlang:",
        reply_markup=list_with_delete_kb(packages, "adm_money_pkg", name_attr="money_amount"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_money_pkg:del:"))
async def adm_money_pkg_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    pkg_id = int(callback.data.split(":")[-1])
    status = await crud.delete_money_package(pkg_id)
    packages = await crud.get_money_packages(active_only=False)
    await callback.message.edit_reply_markup(
        reply_markup=list_with_delete_kb(packages, "adm_money_pkg", name_attr="money_amount")
    )
    if status == "deactivated":
        await callback.answer("⚠️ Bu paket ishlatilgan, shuning uchun butunlay o'chirilmadi - nofaol qilindi", show_alert=True)
    else:
        await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_money_pkg:add")
async def adm_money_pkg_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminMoneyPackage.waiting_money_amount)
    await callback.message.edit_text(
        "💵 Nechta Dollar berilsin? (masalan: 1000)", reply_markup=back_admin_kb("adm:money_prices")
    )
    await callback.answer()


@router.message(AdminMoneyPackage.waiting_money_amount)
async def adm_money_pkg_amount(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:money_prices"))
        return
    await state.update_data(money_amount=int(message.text.strip()))
    await state.set_state(AdminMoneyPackage.waiting_diamond_price)
    await message.answer("💎 Necha Olmosga sotiladi?", reply_markup=back_admin_kb("adm:money_prices"))


@router.message(AdminMoneyPackage.waiting_diamond_price)
async def adm_money_pkg_price(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:money_prices"))
        return
    data = await state.get_data()
    await crud.create_money_package(money_amount=data["money_amount"], diamond_price=int(message.text.strip()))
    await state.clear()
    packages = await crud.get_money_packages(active_only=False)
    await message.answer(
        "✅ Paket qo'shildi!",
        reply_markup=list_with_delete_kb(packages, "adm_money_pkg", name_attr="money_amount"),
    )


# --- Olmos paketlari (karta orqali sotib olish narxlari) ---
@router.callback_query(F.data == "adm:diamond_prices")
async def adm_diamond_prices_list(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    packages = await crud.get_diamond_packages(active_only=False)
    await callback.message.edit_text(
        "💎 <b>Olmos paketlari</b>\n\nKarta orqali necha so'mga nechta olmos berilishini sozlang:",
        reply_markup=list_with_delete_kb(packages, "adm_diamond_pkg", name_attr="diamond_amount"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_diamond_pkg:del:"))
async def adm_diamond_pkg_delete(callback: CallbackQuery):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    pkg_id = int(callback.data.split(":")[-1])
    status = await crud.delete_diamond_package(pkg_id)
    packages = await crud.get_diamond_packages(active_only=False)
    await callback.message.edit_reply_markup(
        reply_markup=list_with_delete_kb(packages, "adm_diamond_pkg", name_attr="diamond_amount")
    )
    if status == "deactivated":
        await callback.answer("⚠️ Bu paket avval sotib olingan, shuning uchun butunlay o'chirilmadi - nofaol qilindi", show_alert=True)
    else:
        await callback.answer("🗑 O'chirildi")


@router.callback_query(F.data == "adm_diamond_pkg:add")
async def adm_diamond_pkg_add_start(callback: CallbackQuery, state: FSMContext):
    if not await is_user_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminDiamondPackage.waiting_price_sum)
    await callback.message.edit_text(
        "💰 Necha so'm turadi? (masalan: 5000)", reply_markup=back_admin_kb("adm:diamond_prices")
    )
    await callback.answer()


@router.message(AdminDiamondPackage.waiting_price_sum)
async def adm_diamond_pkg_price(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:diamond_prices"))
        return
    await state.update_data(price_sum=int(message.text.strip()))
    await state.set_state(AdminDiamondPackage.waiting_diamond_amount)
    await message.answer("💎 Nechta olmos beriladi?", reply_markup=back_admin_kb("adm:diamond_prices"))


@router.message(AdminDiamondPackage.waiting_diamond_amount)
async def adm_diamond_pkg_amount(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring.", reply_markup=back_admin_kb("adm:diamond_prices"))
        return
    data = await state.get_data()
    await crud.create_diamond_package(price_sum=data["price_sum"], diamond_amount=int(message.text.strip()))
    await state.clear()
    packages = await crud.get_diamond_packages(active_only=False)
    await message.answer(
        "✅ Paket qo'shildi!",
        reply_markup=list_with_delete_kb(packages, "adm_diamond_pkg", name_attr="diamond_amount"),
    )
