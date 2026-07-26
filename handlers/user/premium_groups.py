"""
Premium guruhlar bo'limi.

Foydalanuvchining o'z tili/davlati bo'yicha admin panelda saqlangan
premium guruhlar ro'yxati (Top 10, olmos reytingi bo'yicha) ko'rsatiladi.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import premium_groups_kb

router = Router(name="premium_groups")


@router.callback_query(F.data == "open:premium_groups")
async def open_premium_groups(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    lang = user.language or "uz"
    groups = await crud.get_premium_groups(lang)
    groups = groups[:10]
    admin_username = await crud.get_setting("admin_username", "@Hackeruzbekistan001")

    if not groups:
        await callback.message.edit_text(
            t("no_premium_groups", lang),
            reply_markup=premium_groups_kb(lang, [], admin_username),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        t("premium_groups_title", lang),
        reply_markup=premium_groups_kb(lang, groups, admin_username),
    )
    await callback.answer()
