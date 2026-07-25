"""
Para (Pul) menyusi:
  - Tasodifiy pul topish (kunlik limit bilan)
  - Jinsni o'zgartirish (limit bilan)
  - Para (juftlik) topish - qarama-qarshi jinsdan tasodifiy odamga taklif yuboradi
"""
import random

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from config import FREE_MONEY_DAILY_LIMIT, GENDER_CHANGE_LIMIT
from database import crud
from database.models import GenderEnum
from locales.texts import t
from keyboards.user_kb import money_menu_kb
from keyboards.common_kb import yes_no_kb

router = Router(name="money")

RANDOM_MONEY_MIN = 5
RANDOM_MONEY_MAX = 50


async def render_money_menu(user_id: int, lang: str):
    can_use, remaining = await crud.can_use_free_random_money(user_id, FREE_MONEY_DAILY_LIMIT)
    user = await crud.get_user(user_id)
    text = t("no_money_yet", lang, limit=FREE_MONEY_DAILY_LIMIT) if user.money == 0 else t(
        "money_menu_title", lang
    )
    kb = money_menu_kb(lang, used=FREE_MONEY_DAILY_LIMIT - remaining, limit=FREE_MONEY_DAILY_LIMIT)
    return text, kb


@router.callback_query(F.data == "open:money")
async def open_money(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    text, kb = await render_money_menu(callback.from_user.id, user.language)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "random_money")
async def random_money(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    can_use, remaining = await crud.can_use_free_random_money(callback.from_user.id, FREE_MONEY_DAILY_LIMIT)
    if not can_use:
        await callback.answer(t("no_free_tries_left", user.language), show_alert=True)
        return

    amount = random.randint(RANDOM_MONEY_MIN, RANDOM_MONEY_MAX)
    await crud.use_free_random_money(callback.from_user.id, amount)
    await callback.answer(t("random_money_result", user.language, amount=amount), show_alert=True)

    text, kb = await render_money_menu(callback.from_user.id, user.language)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "change_gender")
async def change_gender(callback: CallbackQuery):
    user = await crud.get_user(callback.from_user.id)
    if user.gender_change_count >= GENDER_CHANGE_LIMIT:
        await callback.answer(t("gender_change_limit_reached", user.language), show_alert=True)
        return

    new_gender = GenderEnum.female if user.gender == GenderEnum.male else GenderEnum.male
    await crud.set_user_gender(callback.from_user.id, new_gender, increment_change=True)
    await callback.answer("✅", show_alert=False)

    text, kb = await render_money_menu(callback.from_user.id, user.language)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "find_partner")
async def find_partner(callback: CallbackQuery, bot: Bot):
    user = await crud.get_user(callback.from_user.id)

    if user.gender == GenderEnum.unset:
        await callback.answer("❌", show_alert=True)
        return

    await callback.answer(t("searching_partner", user.language))

    opposite = GenderEnum.female if user.gender == GenderEnum.male else GenderEnum.male
    candidate = await crud.find_random_partner_candidate(callback.from_user.id, opposite)

    if not candidate:
        await callback.message.answer(t("no_candidates_found", user.language))
        return

    req = await crud.create_partner_request(callback.from_user.id, candidate.id)

    sender_name = callback.from_user.first_name or str(callback.from_user.id)
    try:
        await bot.send_message(
            candidate.id,
            t("partner_request_sent_to_target", candidate.language, from_name=sender_name),
            reply_markup=yes_no_kb(
                candidate.language,
                yes_cb=f"partner_resp:accept:{req.id}",
                no_cb=f"partner_resp:decline:{req.id}",
            ),
        )
    except Exception:
        # Foydalanuvchi botni bloklagan bo'lishi mumkin
        pass


@router.callback_query(F.data.startswith("partner_resp:"))
async def partner_response(callback: CallbackQuery, bot: Bot):
    _, action, req_id_str = callback.data.split(":")
    req_id = int(req_id_str)
    accept = action == "accept"

    req = await crud.resolve_partner_request(req_id, accept)
    if not req:
        await callback.answer()
        return

    target_user = await crud.get_user(req.to_user_id)
    sender_user = await crud.get_user(req.from_user_id)
    target_name = callback.from_user.first_name or str(callback.from_user.id)

    if accept:
        await callback.message.edit_text(
            t("partner_you_accepted", target_user.language, from_name=sender_user.first_name or req.from_user_id)
        )
    else:
        await callback.message.edit_text(
            t("partner_you_declined", target_user.language, from_name=sender_user.first_name or req.from_user_id)
        )

    try:
        key = "partner_accepted_notify_sender" if accept else "partner_declined_notify_sender"
        await bot.send_message(
            req.from_user_id,
            t(key, sender_user.language, to_name=target_name),
        )
    except Exception:
        pass

    await callback.answer()
