"""'Mening geroyim' bo'limi - geroylarni ko'rish va sotib olish."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery

from database import crud
from locales.texts import t
from keyboards.user_kb import hero_shop_kb
from keyboards.common_kb import back_kb

router = Router(name="hero")


@router.callback_query(F.data == "open:my_hero")
async def open_my_hero(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    owned_heroes = await crud.get_user_heroes(callback.from_user.id)

    if owned_heroes:
        text = "\n\n".join(
            f"{h.emoji} <b>{h.name}</b>\n💪 {h.abilities_text}\n🛡 {h.protection_text}" for h in owned_heroes
        )
        await callback.message.edit_text(text, reply_markup=back_kb(user.language, "back:profile"))
        await callback.answer()
        return

    heroes = await crud.get_heroes()
    if not heroes:
        await callback.message.edit_text(
            t("no_hero_yet", user.language), reply_markup=back_kb(user.language, "back:profile")
        )
        await callback.answer()
        return

    hero = heroes[0]  # bitta asosiy geroy taklif qilinadi (admin bir nechta qo'shsa, keyingisi qo'shiladi)
    await callback.message.edit_text(
        t("no_hero_yet", user.language), reply_markup=hero_shop_kb(user.language, hero)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_hero_diamond:"))
async def buy_hero_diamond(callback: CallbackQuery):
    hero_id = int(callback.data.split(":", 1)[1])
    user = await crud.get_user(callback.from_user.id)
    hero = await crud.get_hero(hero_id)
    if not hero:
        await callback.answer()
        return

    ok = await crud.buy_hero(callback.from_user.id, hero, pay_with="diamond")
    if not ok:
        await callback.answer(t("not_enough_balance", user.language), show_alert=True)
        return

    await crud.set_active_hero(callback.from_user.id, hero.id)
    await callback.answer(t("hero_bought", user.language, hero_name=hero.name), show_alert=True)
    await callback.message.edit_text(
        f"{hero.emoji} <b>{hero.name}</b>\n💪 {hero.abilities_text}\n🛡 {hero.protection_text}",
        reply_markup=back_kb(user.language, "back:profile"),
    )


@router.callback_query(F.data.startswith("buy_hero_stars:"))
async def buy_hero_stars(callback: CallbackQuery):
    """Telegram Stars orqali to'lov (haqiqiy invoys yuborish)."""
    hero_id = int(callback.data.split(":", 1)[1])
    hero = await crud.get_hero(hero_id)
    if not hero:
        await callback.answer()
        return

    await callback.message.answer_invoice(
        title=hero.name,
        description=hero.abilities_text[:250],
        payload=f"hero:{hero.id}:{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=hero.name, amount=hero.price_stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message):
    payload = message.successful_payment.invoice_payload
    _, hero_id_str, user_id_str = payload.split(":")
    hero_id = int(hero_id_str)
    user_id = int(user_id_str)

    hero = await crud.get_hero(hero_id)
    from database.db import async_session
    from database.models import UserHero
    async with async_session() as s:
        s.add(UserHero(user_id=user_id, hero_id=hero_id))
        await s.commit()
    await crud.set_active_hero(user_id, hero_id)

    user = await crud.get_user(user_id)
    await message.answer(t("hero_bought", user.language, hero_name=hero.name))
