"""/roles komandasi - barcha rollar ro'yxati va ularning tavsifi."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import roles_list_kb
from keyboards.common_kb import back_kb

router = Router(name="roles_info")


@router.message(Command("roles"))
async def cmd_roles(message: Message):
    user = await crud.get_user(message.from_user.id)
    lang = user.language if user else "uz"
    roles = await crud.get_roles()
    if not roles:
        await message.answer("Hozircha rollar sozlanmagan.")
        return
    await message.answer(t("roles_list_title", lang), reply_markup=roles_list_kb(roles))


@router.callback_query(F.data.startswith("role_info:"))
async def role_info(callback: CallbackQuery):
    role_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    lang = user.language if user else "uz"
    role = await crud.get_role(role_id)
    if not role:
        await callback.answer()
        return
    await callback.message.edit_text(
        t("role_detail", lang, emoji=role.emoji, name=role.name, description=role.description),
        reply_markup=back_kb(lang, "back:roles_list"),
    )
    await callback.answer()


@router.callback_query(F.data == "back:roles_list")
async def back_to_roles_list(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    lang = user.language if user else "uz"
    roles = await crud.get_roles()
    await callback.message.edit_text(t("roles_list_title", lang), reply_markup=roles_list_kb(roles))
    await callback.answer()
