"""Admin panel uchun inline klaviaturalar."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Foydalanuvchini qidirish", callback_data="adm:search_user")
    builder.button(text="🛒 Do'kon (Himoyalar)", callback_data="adm:shop")
    builder.button(text="🦸 Geroylar", callback_data="adm:heroes")
    builder.button(text="🎭 Rollar", callback_data="adm:roles")
    builder.button(text="🎯 O'yin rejimlari", callback_data="adm:game_modes")
    builder.button(text="💎 Premium guruhlar", callback_data="adm:premium_groups")
    builder.button(text="💵 Pul narxlari", callback_data="adm:money_prices")
    builder.button(text="💎 Olmos paketlari", callback_data="adm:diamond_prices")
    builder.button(text="🧾 Olmos so'rovlari", callback_data="adm:diamond_requests")
    builder.button(text="🏆 Mukofot sozlamalari", callback_data="adm:rewards")
    builder.button(text="👤 Admin username", callback_data="adm:admin_username")
    builder.button(text="💳 Karta raqami", callback_data="adm:card_number")
    builder.button(text="👮 Adminlar", callback_data="adm:admins")
    builder.button(text="📊 Statistika", callback_data="adm:stats")
    builder.button(text="⬅️ Chiqish", callback_data="back:main")
    builder.adjust(1, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def back_admin_kb(cb: str = "adm:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Orqaga", callback_data=cb)
    return builder.as_markup()


def list_with_delete_kb(items: list, prefix: str, name_attr: str = "name", back_cb: str = "adm:main") -> InlineKeyboardMarkup:
    """items ro'yxatini chiqaradi, har biriga o'chirish tugmasi bilan."""
    builder = InlineKeyboardBuilder()
    for item in items:
        name = getattr(item, name_attr, str(item.id))
        builder.button(text=f"🗑 {name}", callback_data=f"{prefix}:del:{item.id}")
    builder.button(text="➕ Qo'shish", callback_data=f"{prefix}:add")
    builder.button(text="↩️ Orqaga", callback_data=back_cb)
    builder.adjust(1)
    return builder.as_markup()


def premium_groups_list_kb(items: list, back_cb: str = "adm:premium_groups") -> InlineKeyboardMarkup:
    """Premium guruhlar ro'yxati -- har bir guruh nomi yonida admin kiritgan olmos miqdori ko'rsatiladi."""
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"🗑 {item.name} — 💎 {item.diamond_rank}",
            callback_data=f"adm_pg:del:{item.id}",
        )
    builder.button(text="➕ Qo'shish", callback_data="adm_pg:add")
    builder.button(text="↩️ Orqaga", callback_data=back_cb)
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=yes_cb)
    builder.button(text="❌ Bekor qilish", callback_data=no_cb)
    builder.adjust(2)
    return builder.as_markup()


def user_management_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💵 Pul qo'shish", callback_data=f"adm:user_money_add:{user_id}")
    builder.button(text="💵 Pul ayirish", callback_data=f"adm:user_money_sub:{user_id}")
    builder.button(text="💎 Olmos qo'shish", callback_data=f"adm:user_diamond_add:{user_id}")
    builder.button(text="💎 Olmos ayirish", callback_data=f"adm:user_diamond_sub:{user_id}")
    builder.button(text="🚫 Ban/Unban", callback_data=f"adm:user_ban:{user_id}")
    builder.button(text="↩️ Orqaga", callback_data="adm:main")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def diamond_request_review_kb(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"adm:dreq_approve:{request_id}")
    builder.button(text="❌ Rad etish", callback_data=f"adm:dreq_reject:{request_id}")
    builder.adjust(2)
    return builder.as_markup()


def role_team_select_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔪 Mafiya", callback_data="role_team:mafia")
    builder.button(text="🕊 Tinch aholi", callback_data="role_team:peaceful")
    builder.button(text="🎯 Yakka", callback_data="role_team:solo")
    builder.adjust(1)
    return builder.as_markup()


def role_action_select_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    actions = [
        ("none", "Yo'q"), ("kill", "O'ldirish"), ("heal", "Davolash"),
        ("check", "Tekshirish"), ("block", "Bloklash"), ("revive", "Tiriltirish"),
        ("protect", "Himoya qilish"), ("custom", "Faqat matn (avtomatikasiz)"),
    ]
    for code, name in actions:
        builder.button(text=name, callback_data=f"role_action:{code}")
    builder.adjust(2)
    return builder.as_markup()


def protection_type_select_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    types = [
        ("hujjat", "📄 Hujjat"), ("osishdan_himoya", "🪂 Osishdan himoya"),
        ("qotildan_himoya", "🩸 Qotildan himoya"), ("miltiq", "🔫 Miltiq"),
        ("doridan_himoya", "🧪 Doridan himoya"), ("maska", "🎭 Maska"),
        ("sirpanishdan_himoya", "🥷 Sirpanishdan himoya"), ("qahramon_himoyasi", "📗 Qahramon himoyasi"),
    ]
    for code, name in types:
        builder.button(text=name, callback_data=f"protection_type:{code}")
    builder.adjust(2)
    return builder.as_markup()


def language_pick_for_group_kb() -> InlineKeyboardMarkup:
    from config import LANGUAGES
    builder = InlineKeyboardBuilder()
    for code, (flag, name) in LANGUAGES.items():
        builder.button(text=f"{flag} {name}", callback_data=f"pg_country:{code}")
    builder.adjust(2)
    return builder.as_markup()
