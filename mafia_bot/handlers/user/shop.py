"""Do'kon (Himoyalar buyumlari) - foydalanuvchi sotib olishi."""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import shop_kb

router = Router(name="shop")


@router.callback_query(F.data == "open:shop")
async def open_shop(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    items = await crud.get_shop_items()
    await callback.message.edit_text(
        t("shop_title", user.language),
        reply_markup=shop_kb(user.language, items),
    )
    await callback.answer()


@router.callback_query(F.data == "open:diamond_shop")
async def open_diamond_category_shop(callback: CallbackQuery):
    """Profildagi 1-chi 'Xarid qilish' tugmasi - 'himoya' kategoriyasi."""
    user = await crud.get_user(callback.from_user.id)
    items = await crud.get_shop_items(category="himoya")
    await callback.message.edit_text(
        t("shop_title", user.language),
        reply_markup=shop_kb(user.language, items),
    )
    await callback.answer()


@router.callback_query(F.data == "open:money_shop")
async def open_weapon_category_shop(callback: CallbackQuery):
    """Profildagi 2-chi 'Xarid qilish' tugmasi - 'qurol' kategoriyasi."""
    user = await crud.get_user(callback.from_user.id)
    items = await crud.get_shop_items(category="qurol")
    await callback.message.edit_text(
        t("shop_title", user.language),
        reply_markup=shop_kb(user.language, items),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_item:"))
async def buy_item(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    item = await crud.get_shop_item(item_id)
    user = await crud.get_user(callback.from_user.id)

    if not item:
        await callback.answer()
        return

    pay_with = "money" if item.price_money else "diamond"
    ok = await crud.purchase_shop_item(callback.from_user.id, item, pay_with=pay_with)

    if not ok:
        await callback.answer(t("not_enough_balance", user.language), show_alert=True)
        return

    await callback.answer(t("shop_item_bought", user.language, item_name=item.name), show_alert=True)
    items = await crud.get_shop_items()
    await callback.message.edit_reply_markup(reply_markup=shop_kb(user.language, items))
