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
    builder.adjust(1, 2, 2, 2, 2, 2, 2, 1, 1)
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


ROLE_ACTION_LABELS = [
    ("none", "Yo'q"), ("kill", "O'ldirish"), ("heal", "Davolash"),
    ("check", "Tekshirish"), ("block", "Bloklash"), ("revive", "Tiriltirish"),
    ("protect", "Himoya qilish"), ("custom", "Faqat matn (avtomatikasiz)"),
]
ROLE_TEAM_LABELS = [("mafia", "🔪 Mafiya"), ("peaceful", "🕊 Tinch aholi"), ("solo", "🎯 Yakka")]


def role_action_select_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in ROLE_ACTION_LABELS:
        builder.button(text=name, callback_data=f"role_action:{code}")
    builder.adjust(2)
    return builder.as_markup()


def role_list_view_kb(items: list, back_cb: str = "adm:main") -> InlineKeyboardMarkup:
    """Rollar ro'yxati -- bosilsa TO'G'RIDAN-TO'G'RI o'chirmaydi, balki tahrirlash/o'chirish
    menyusini ochadi (adm_role:view:{id})."""
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"{item.emoji} {item.name}", callback_data=f"adm_role:view:{item.id}")
    builder.button(text="➕ Qo'shish", callback_data="adm_role:add")
    builder.button(text="↩️ Orqaga", callback_data=back_cb)
    builder.adjust(1)
    return builder.as_markup()


def role_view_kb(role) -> InlineKeyboardMarkup:
    """Bitta rolning barcha sozlamalarini ko'rsatib, har birini alohida tahrirlash imkonini beradi."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⚔️ Jamoa: {role.team.value}", callback_data=f"role_edit_team_open:{role.id}")
    builder.button(text=f"🌙 Tungi harakat: {role.night_action_type.value}", callback_data=f"role_edit_action_open:{role.id}")
    builder.button(
        text=f"👑 Jamoa boshlig'i: {'✅ Ha' if role.is_team_boss else '❌ Yo\'q'}",
        callback_data=f"role_edit_toggle:{role.id}:is_team_boss",
    )
    builder.button(
        text=f"🗡 Mustaqil o'ldiradi: {'✅ Ha' if role.acts_independently else '❌ Yo\'q'}",
        callback_data=f"role_edit_toggle:{role.id}:acts_independently",
    )
    builder.button(
        text=f"🔀 Tekshirish/Otish (dual): {'✅ Ha' if role.dual_check_or_kill else '❌ Yo\'q'}",
        callback_data=f"role_edit_toggle:{role.id}:dual_check_or_kill",
    )
    builder.button(text=f"🔢 Bittaga soni: {role.max_per_game}", callback_data=f"role_edit_max:{role.id}")
    builder.button(text=f"💎 Sotib olish narxi: {role.price_diamond}", callback_data=f"role_edit_price:{role.id}")
    builder.button(text=f"🎲 Rejim: {role.mode}", callback_data=f"role_edit_mode:{role.id}")
    builder.button(text="✍️ Tavsifni o'zgartirish", callback_data=f"role_edit_desc:{role.id}")
    succ_label = "❌ yo'q" if not role.succeeds_role_id else "✅ belgilangan"
    builder.button(text=f"🔁 Kimning o'rnini bosadi: {succ_label}", callback_data=f"role_edit_succ_open:{role.id}")
    active_label = "✅ Faol" if role.is_active else "🚫 Nofaol"
    builder.button(text=f"🔘 Holati: {active_label}", callback_data=f"role_edit_toggle:{role.id}:is_active")
    builder.button(text="🗑 O'chirish", callback_data=f"adm_role:del:{role.id}")
    builder.button(text="↩️ Orqaga", callback_data="adm:roles")
    builder.adjust(1)
    return builder.as_markup()


def role_team_edit_kb(role_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in ROLE_TEAM_LABELS:
        builder.button(text=label, callback_data=f"role_edit_team_set:{role_id}:{code}")
    builder.button(text="↩️ Bekor qilish", callback_data=f"adm_role:view:{role_id}")
    builder.adjust(1)
    return builder.as_markup()


def role_action_edit_kb(role_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in ROLE_ACTION_LABELS:
        builder.button(text=name, callback_data=f"role_edit_action_set:{role_id}:{code}")
    builder.button(text="↩️ Bekor qilish", callback_data=f"adm_role:view:{role_id}")
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
