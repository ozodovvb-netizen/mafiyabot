"""
Olmos (diamond) sotib olish (profildagi 1-chi "Xarid qilish" tugmasi):
  1. Foydalanuvchi paket tanlaydi (masalan 1000 so'm - 1 olmos)
  2. Bot karta raqamini ko'rsatadi
  3. Foydalanuvchi to'lov chekini (screenshot) yuboradi
  4. So'rov admin(lar)ga yuboriladi, tasdiqlansa olmos hisobga qo'shiladi
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import SUPER_ADMINS
from database import crud
from locales.texts import t
from keyboards.user_kb import diamond_packages_kb
from keyboards.admin_kb import diamond_request_review_kb
from states.states import DiamondTopupStates

router = Router(name="diamonds")


@router.callback_query(F.data == "open:buy_diamonds")
async def open_diamond_packages(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    packages = await crud.get_diamond_packages()
    if not packages:
        await callback.answer("Hozircha paketlar mavjud emas, admin hali sozlamagan.", show_alert=True)
        return
    await callback.message.edit_text(
        t("diamond_menu_title", user.language),
        reply_markup=diamond_packages_kb(user.language, packages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("diamond_pkg:"))
async def choose_diamond_package(callback: CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    card_number = await crud.get_setting("payment_card_number", "8600 XXXX XXXX XXXX")

    packages = await crud.get_diamond_packages()
    pkg = next((p for p in packages if p.id == pkg_id), None)
    if not pkg:
        await callback.answer()
        return

    await state.update_data(diamond_package_id=pkg.id)
    await state.set_state(DiamondTopupStates.waiting_receipt)

    await callback.message.edit_text(
        t(
            "diamond_send_receipt", user.language,
            price=pkg.price_sum, diamonds=pkg.diamond_amount, card_number=card_number,
        )
    )
    await callback.answer()


@router.message(DiamondTopupStates.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pkg_id = data.get("diamond_package_id")
    user = await crud.get_user(message.from_user.id)

    file_id = message.photo[-1].file_id
    req = await crud.create_diamond_topup_request(message.from_user.id, pkg_id, file_id)

    await message.answer(t("receipt_received", user.language))
    await state.clear()

    # Adminlarga yuborish (chek + tasdiqlash tugmalari)
    packages = await crud.get_diamond_packages()
    pkg = next((p for p in packages if p.id == pkg_id), None)
    caption = (
        f"🧾 Yangi olmos to'ldirish so'rovi #{req.id}\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"💰 {pkg.price_sum if pkg else '?'} so'm → 💎 {pkg.diamond_amount if pkg else '?'}"
    )
    for admin_id in SUPER_ADMINS:
        try:
            await bot.send_photo(
                admin_id, file_id, caption=caption,
                reply_markup=diamond_request_review_kb(req.id),
            )
        except Exception:
            pass
