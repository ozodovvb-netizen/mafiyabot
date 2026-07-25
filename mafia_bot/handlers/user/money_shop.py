"""Profildagi 2-chi 'Xarid qilish' tugmasi: olmos evaziga dollar sotib olish."""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import money_packages_kb

router = Router(name="money_shop")


@router.callback_query(F.data == "open:buy_money")
async def open_money_packages(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    packages = await crud.get_money_packages()
    if not packages:
        await callback.answer("Hozircha paketlar mavjud emas, admin hali sozlamagan.", show_alert=True)
        return
    await callback.message.edit_text(
        t("money_shop_title", user.language),
        reply_markup=money_packages_kb(user.language, packages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("money_pkg:"))
async def buy_money_package(callback: CallbackQuery):
    pkg_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    packages = await crud.get_money_packages()
    pkg = next((p for p in packages if p.id == pkg_id), None)
    if not pkg:
        await callback.answer()
        return

    if user.diamonds < pkg.diamond_price:
        await callback.answer(t("not_enough_balance", user.language), show_alert=True)
        return

    await crud.update_user_balance(callback.from_user.id, money_delta=pkg.money_amount, diamond_delta=-pkg.diamond_price)
    await callback.answer(t("money_bought", user.language, money=pkg.money_amount), show_alert=True)

    packages = await crud.get_money_packages()
    await callback.message.edit_reply_markup(reply_markup=money_packages_kb(user.language, packages))
