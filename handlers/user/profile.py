"""/profile komandasi - foydalanuvchi profilini to'liq ko'rsatadi."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import profile_menu_kb
from utils.helpers import full_name

router = Router(name="profile")


async def render_profile_text(user_id: int, lang: str, display_name: str) -> str:
    user = await crud.get_user(user_id)
    news_channel = await crud.get_setting("news_channel", "@AgencyMafiaa")

    active_role_name = t("no_role", lang)
    if user.active_hero_id:
        hero = await crud.get_hero(user.active_hero_id)
        if hero:
            active_role_name = f"{hero.emoji} {hero.name}"

    partner_text = t("no_partner", lang)
    if user.partner_id:
        partner = await crud.get_user(user.partner_id)
        if partner:
            partner_text = partner.first_name or str(partner.id)

    return t(
        "profile_text", lang,
        name=display_name,
        money=user.money,
        diamonds=user.diamonds,
        himoya=user.himoya_qty,
        hujjat=user.hujjat_qty,
        osishdan=user.osishdan_himoya_qty,
        qotildan=user.qotildan_himoya_qty,
        miltiq=user.miltiq_qty,
        doridan=user.doridan_himoya_qty,
        maska=user.maska_qty,
        sirpanish=user.sirpanishdan_himoya_qty,
        qahramon=user.qahramon_himoyasi_qty,
        wins=user.wins,
        total_games=user.total_games,
        active_role=active_role_name,
        partner=partner_text,
        news_channel=news_channel,
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    tg_user = message.from_user
    user, _ = await crud.get_or_create_user(tg_user.id, tg_user.username, full_name(tg_user))
    if not user.language:
        from keyboards.common_kb import language_kb
        await message.answer(t("choose_language", None), reply_markup=language_kb())
        return
    text = await render_profile_text(tg_user.id, user.language, full_name(tg_user))
    await message.answer(text, reply_markup=profile_menu_kb(user.language))


@router.callback_query(F.data == "back:profile")
async def back_to_profile(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    text = await render_profile_text(callback.from_user.id, user.language, full_name(callback.from_user))
    await callback.message.edit_text(text, reply_markup=profile_menu_kb(user.language))
    await callback.answer()
