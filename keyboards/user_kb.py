"""Foydalanuvchi tomon (start, profil, do'kon, himoyalar...) klaviaturalari."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from locales.texts import t
from database.models import ShopItem, Hero, ProtectionType, User


def start_menu_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_add_to_group", lang),
        url=f"https://t.me/{config.BOT_USERNAME}?startgroup=true",
    )
    builder.button(text=t("btn_questions", lang), callback_data="open:questions")
    builder.button(text=t("btn_premium_groups", lang), callback_data="open:premium_groups")
    builder.adjust(1, 2)
    return builder.as_markup()


def profile_menu_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_himoyalar", lang), callback_data="open:protections")
    builder.button(text=t("btn_para", lang), callback_data="open:money")
    builder.button(text=t("btn_dokon", lang), callback_data="open:shop")
    builder.button(text=t("btn_xarid_qilish", lang), callback_data="open:buy_diamonds")
    builder.button(text=t("btn_xarid_qilish", lang), callback_data="open:buy_money")
    builder.button(text=t("btn_mening_geroyim", lang), callback_data="open:my_hero")
    builder.button(text=t("btn_premium_groups", lang), callback_data="open:premium_groups")
    builder.button(text=t("btn_change_language", lang), callback_data="open:change_language")
    builder.adjust(1, 2, 2, 2, 1)
    return builder.as_markup()


def protections_kb(lang: str, user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = [
        (ProtectionType.himoya if False else None, None),  # placeholder not used
    ]
    mapping = [
        ("🛡", "himoya_on", "himoya"),
        ("📄", "hujjat_on", "hujjat"),
        ("🪂", "osishdan_himoya_on", "osishdan_himoya"),
        ("🩸", "qotildan_himoya_on", "qotildan_himoya"),
        ("🌾", "miltiq_on", "miltiq"),
        ("🧪", "doridan_himoya_on", "doridan_himoya"),
        ("🎭", "maska_on", "maska"),
        ("🥷", "sirpanishdan_himoya_on", "sirpanishdan_himoya"),
    ]
    for emoji, field, code in mapping:
        state = t("on", lang) if getattr(user, field) else t("off", lang)
        builder.button(text=f"{emoji} — {state}", callback_data=f"toggle_protection:{field}")
    builder.button(
        text=f"{t('btn_faol_rol', lang)} — {(t('on', lang) if user.faol_rol_on else t('off', lang))}",
        callback_data="toggle_protection:faol_rol_on",
    )
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def shop_kb(lang: str, items: list[ShopItem]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        price = f"{item.price_money}💵" if item.price_money else f"{item.price_diamond}💎"
        builder.button(text=f"{item.emoji} {item.name} — {price}", callback_data=f"buy_item:{item.id}")
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(1)
    return builder.as_markup()


def money_menu_kb(lang: str, used: int, limit: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_random_money", lang), callback_data="random_money")
    builder.button(text=t("btn_find_partner", lang), callback_data="find_partner")
    builder.button(
        text=t("btn_change_gender", lang, used=used, limit=limit),
        callback_data="change_gender",
    )
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(1)
    return builder.as_markup()


def hero_shop_kb(lang: str, hero: Hero) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("btn_buy_hero_diamond", lang, price=hero.price_diamond),
        callback_data=f"buy_hero_diamond:{hero.id}",
    )
    builder.button(
        text=t("btn_buy_hero_stars", lang, price=hero.price_stars),
        callback_data=f"buy_hero_stars:{hero.id}",
    )
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(1)
    return builder.as_markup()


def diamond_packages_kb(lang: str, packages) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        builder.button(
            text=f"💰 {pkg.price_sum} - 💎 {pkg.diamond_amount}",
            callback_data=f"diamond_pkg:{pkg.id}",
        )
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(2)
    return builder.as_markup()


def money_packages_kb(lang: str, packages) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        builder.button(
            text=f"💵 {pkg.money_amount} - 💎{pkg.diamond_price}",
            callback_data=f"money_pkg:{pkg.id}",
        )
    builder.button(text=t("btn_back", lang), callback_data="back:profile")
    builder.adjust(2)
    return builder.as_markup()


def premium_groups_kb(lang: str, groups) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, g in enumerate(groups, start=1):
        builder.button(text=f"{i}. {g.name}", url=g.link)
    builder.button(text=t("btn_back", lang), callback_data="back:main")
    builder.adjust(1)
    return builder.as_markup()


def roles_list_kb(roles) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for r in roles:
        builder.button(text=f"{r.emoji} {r.name}", callback_data=f"role_info:{r.id}")
    builder.adjust(2)
    return builder.as_markup()


def language_switch_only_kb() -> InlineKeyboardMarkup:
    from keyboards.common_kb import language_kb
    return language_kb()
