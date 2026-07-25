"""Himoyalar bo'limi - foydalanuvchi sotib olgan buyumlarini ON/OFF qiladi."""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import protections_kb

router = Router(name="protections")


@router.callback_query(F.data == "open:protections")
async def open_protections(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    await callback.message.edit_text(
        t("protections_title", user.language),
        reply_markup=protections_kb(user.language, user),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_protection:"))
async def toggle_protection(callback: CallbackQuery):
    field = callback.data.split(":", 1)[1]
    await crud.toggle_protection(callback.from_user.id, field)
    user = await crud.get_user(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=protections_kb(user.language, user))
    await callback.answer()
