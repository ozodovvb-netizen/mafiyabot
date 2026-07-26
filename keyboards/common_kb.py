"""Umumiy (til tanlash, ha/yo'q, orqaga) klaviaturalar."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import LANGUAGES
from locales.texts import t


def language_kb(prefix: str = "lang") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, (flag, name) in LANGUAGES.items():
        builder.button(text=f"{flag} {name}", callback_data=f"{prefix}:{code}")
    builder.adjust(2)
    return builder.as_markup()


def gender_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("gender_male", lang), callback_data="gender:male")
    builder.button(text=t("gender_female", lang), callback_data="gender:female")
    builder.adjust(2)
    return builder.as_markup()


def yes_no_kb(lang: str, yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_yes", lang), callback_data=yes_cb)
    builder.button(text=t("btn_no", lang), callback_data=no_cb)
    builder.adjust(2)
    return builder.as_markup()


def back_kb(lang: str, back_cb: str = "back:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back", lang), callback_data=back_cb)
    return builder.as_markup()


def with_back_button(builder: InlineKeyboardBuilder, lang: str, back_cb: str = "back:main"):
    builder.button(text=t("btn_back", lang), callback_data=back_cb)
    return builder
