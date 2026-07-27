"""/roles komandasi - barcha rollar ro'yxati va ularning tavsifi."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import crud
from locales.texts import t
from keyboards.user_kb import roles_list_kb

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


def _role_detail_kb(lang: str, role) -> "InlineKeyboardBuilder":
    builder = InlineKeyboardBuilder()
    if role.price_diamond > 0:
        builder.button(
            text=f"💎 Faol rol sifatida sotib olish — {role.price_diamond}💎",
            callback_data=f"buy_role:{role.id}",
        )
    builder.button(text=t("btn_back", lang), callback_data="back:roles_list")
    builder.adjust(1)
    return builder


@router.callback_query(F.data.startswith("role_info:"))
async def role_info(callback: CallbackQuery):
    role_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    lang = user.language if user else "uz"
    role = await crud.get_role(role_id)
    if not role:
        await callback.answer()
        return
    extra = ""
    if role.price_diamond > 0:
        reserved_count = await crud.count_role_reservations(role.id)
        extra = (
            f"\n\n💎 Do'kondan {role.price_diamond}💎 ga sotib olib, KEYINGI o'yinda aynan shu "
            f"rolda o'ynashingiz mumkin!\n"
            f"📊 Hozir band qilganlar: {reserved_count} kishi (bitta o'yinda shu roldan "
            f"faqat {role.max_per_game} tasi bo'ladi — agar siz bilan bir o'yinga tushgan "
            f"boshqa band qilgan o'yinchilar ko'p bo'lsa, chegaradan oshib ketganlari "
            f"o'sha safar oddiy tasodifiy rolga tushadi)."
        )
    await callback.message.edit_text(
        t("role_detail", lang, emoji=role.emoji, name=role.name, description=role.description) + extra,
        reply_markup=_role_detail_kb(lang, role).as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_role:"))
async def buy_role(callback: CallbackQuery):
    role_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    lang = user.language if user else "uz"
    status = await crud.reserve_role(callback.from_user.id, role_id)
    if status == "ok":
        role = await crud.get_role(role_id)
        await callback.answer(
            f"✅ {role.emoji} {role.name} band qilindi! Keyingi o'yinda shu rolda o'ynaysiz.",
            show_alert=True,
        )
    elif status == "insufficient":
        await callback.answer(t("not_enough_balance", lang), show_alert=True)
    elif status == "not_purchasable":
        await callback.answer("❌ Bu rol sotilmaydi.", show_alert=True)
    elif status == "already_reserved":
        await callback.answer("ℹ️ Siz bu rolni allaqachon band qilgansiz.", show_alert=True)
    else:
        await callback.answer("❌ Rol topilmadi.", show_alert=True)


@router.callback_query(F.data == "back:roles_list")
async def back_to_roles_list(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    lang = user.language if user else "uz"
    roles = await crud.get_roles()
    await callback.message.edit_text(t("roles_list_title", lang), reply_markup=roles_list_kb(roles))
    await callback.answer()
