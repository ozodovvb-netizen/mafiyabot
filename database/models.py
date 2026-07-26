"""
PostgreSQL uchun SQLAlchemy (async) modellari.
Har bir jadval loyihadagi bitta bo'limga mos keladi.
"""
from datetime import datetime, date
import enum

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, ForeignKey, DateTime, Date,
    Text, Float, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ENUM turlari
# ---------------------------------------------------------------------------
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    unset = "unset"


class RoleTeam(str, enum.Enum):
    mafia = "mafia"          # Mafiya jamoasi
    peaceful = "peaceful"    # Tinch aholi jamoasi
    solo = "solo"            # Yakka o'ynovchi (Yollanma qotil, Jurnalist va h.k.)


class NightActionType(str, enum.Enum):
    none = "none"
    kill = "kill"            # o'ldirish (Mafia, Don, Yollanma qotil...)
    heal = "heal"            # davolash (Doktor)
    check = "check"          # tekshirish (Komissar)
    block = "block"          # bloklash / uxlatish (Sehrgar)
    revive = "revive"        # tiriltirish
    protect = "protect"      # himoya qilish (Serjant/Bodyguard)
    custom = "custom"        # faqat matn - avtomatik mexanika yo'q, hikoya/rol-play uchun


class ProtectionType(str, enum.Enum):
    osishdan_himoya = "osishdan_himoya"     # osishdan (linch/ovoz) himoya
    qotildan_himoya = "qotildan_himoya"     # tunda o'ldirilishdan himoya
    doridan_himoya = "doridan_himoya"       # zaharlanishdan himoya
    sirpanishdan_himoya = "sirpanishdan_himoya"  # tekshiruvdan (komissar) himoya
    qahramon_himoyasi = "qahramon_himoyasi"      # geroy hujumidan himoya
    miltiq = "miltiq"                       # qurol - tunda o'ziga hujum qilganni ota oladi
    maska = "maska"                         # rolni yashiradi
    hujjat = "hujjat"                       # soxta hujjat - boshqa kimningdir o'rnida ko'rinish


class DiamondRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class GameStatus(str, enum.Enum):
    registration = "registration"
    night = "night"
    day_discussion = "day_discussion"
    voting = "voting"
    finished = "finished"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# FOYDALANUVCHI
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # telegram user_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    language: Mapped[str | None] = mapped_column(String(8), nullable=True)  # None => hali tanlamagan
    gender: Mapped[GenderEnum] = mapped_column(SAEnum(GenderEnum), default=GenderEnum.unset)
    gender_change_count: Mapped[int] = mapped_column(Integer, default=0)  # nechta marta o'zgartirgan

    money: Mapped[int] = mapped_column(BigInteger, default=0)       # Dollar
    diamonds: Mapped[int] = mapped_column(Integer, default=0)       # Olmos

    # --- Himoyalar soni (necha marta ishlatilishi mumkinligi) va ON/OFF holati ---
    himoya_qty: Mapped[int] = mapped_column(Integer, default=0)             # umumiy "Himoya" (щит) soni
    hujjat_qty: Mapped[int] = mapped_column(Integer, default=0)
    osishdan_himoya_qty: Mapped[int] = mapped_column(Integer, default=0)
    qotildan_himoya_qty: Mapped[int] = mapped_column(Integer, default=0)
    miltiq_qty: Mapped[int] = mapped_column(Integer, default=0)
    doridan_himoya_qty: Mapped[int] = mapped_column(Integer, default=0)
    maska_qty: Mapped[int] = mapped_column(Integer, default=0)
    sirpanishdan_himoya_qty: Mapped[int] = mapped_column(Integer, default=0)
    qahramon_himoyasi_qty: Mapped[int] = mapped_column(Integer, default=0)

    # Har bir himoya turi uchun ON/OFF (o'yinda ishlatilishini xohlaydimi)
    himoya_on: Mapped[bool] = mapped_column(Boolean, default=True)
    hujjat_on: Mapped[bool] = mapped_column(Boolean, default=True)
    osishdan_himoya_on: Mapped[bool] = mapped_column(Boolean, default=True)
    qotildan_himoya_on: Mapped[bool] = mapped_column(Boolean, default=True)
    miltiq_on: Mapped[bool] = mapped_column(Boolean, default=True)
    doridan_himoya_on: Mapped[bool] = mapped_column(Boolean, default=True)
    maska_on: Mapped[bool] = mapped_column(Boolean, default=True)
    sirpanishdan_himoya_on: Mapped[bool] = mapped_column(Boolean, default=True)
    qahramon_himoyasi_on: Mapped[bool] = mapped_column(Boolean, default=True)
    faol_rol_on: Mapped[bool] = mapped_column(Boolean, default=True)  # "Faol rol - ON/OFF"

    active_hero_id: Mapped[int | None] = mapped_column(ForeignKey("heroes.id"), nullable=True)

    wins: Mapped[int] = mapped_column(Integer, default=0)
    total_games: Mapped[int] = mapped_column(Integer, default=0)

    partner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # juftlik

    free_random_money_used_today: Mapped[int] = mapped_column(Integer, default=0)
    free_random_money_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    active_hero = relationship("Hero", foreign_keys=[active_hero_id])

    def get_qty(self, protection: ProtectionType) -> int:
        return getattr(self, f"{protection.value}_qty")

    def get_on(self, protection: ProtectionType) -> bool:
        return getattr(self, f"{protection.value}_on")


# ---------------------------------------------------------------------------
# DO'KON (Himoyalar)
# ---------------------------------------------------------------------------
class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    emoji: Mapped[str] = mapped_column(String(16), default="🛡")
    protection_type: Mapped[ProtectionType] = mapped_column(SAEnum(ProtectionType))
    description: Mapped[str] = mapped_column(Text)  # "nimadan himoya qiladi" - admin yozadi
    price_money: Mapped[int] = mapped_column(BigInteger, default=0)      # Dollarda narx
    price_diamond: Mapped[int] = mapped_column(Integer, default=0)      # Olmosda narx (0 bo'lishi mumkin)
    category: Mapped[str] = mapped_column(String(32), default="himoya")  # "himoya" | "qurol" (2 ta Xarid qilish tugmasi uchun)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------------------
# GEROYLAR
# ---------------------------------------------------------------------------
class Hero(Base):
    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    emoji: Mapped[str] = mapped_column(String(16), default="🦸")
    price_diamond: Mapped[int] = mapped_column(Integer, default=90)
    price_stars: Mapped[int] = mapped_column(Integer, default=250)
    abilities_text: Mapped[str] = mapped_column(Text)     # "nima qila oladi" - admin yozadi
    protection_text: Mapped[str] = mapped_column(Text)    # "nimadan himoyalaydi" - admin yozadi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserHero(Base):
    __tablename__ = "user_heroes"
    __table_args__ = (UniqueConstraint("user_id", "hero_id", name="uq_user_hero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    hero_id: Mapped[int] = mapped_column(ForeignKey("heroes.id"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# ROLLAR (o'yin rollari, admin panel orqali boshqariladi)
# ---------------------------------------------------------------------------
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    emoji: Mapped[str] = mapped_column(String(16), default="🎭")
    team: Mapped[RoleTeam] = mapped_column(SAEnum(RoleTeam))
    night_action_type: Mapped[NightActionType] = mapped_column(SAEnum(NightActionType), default=NightActionType.none)
    description: Mapped[str] = mapped_column(Text)  # "bu rol nima qila oladi" - /roles bosilganda chiqadi
    min_players_required: Mapped[int] = mapped_column(Integer, default=0)  # nechta o'yinchidan boshlab qatnashadi
    max_per_game: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # tungi harakat tartibi (kichik son oldin ishlaydi)


# ---------------------------------------------------------------------------
# GURUH SOZLAMALARI (har bir guruh uchun til va h.k.)
# ---------------------------------------------------------------------------
class GroupSetting(Base):
    __tablename__ = "group_settings"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language: Mapped[str] = mapped_column(String(8), default="uz")


# ---------------------------------------------------------------------------
# PREMIUM GURUHLAR
# ---------------------------------------------------------------------------
class PremiumGroup(Base):
    __tablename__ = "premium_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(8))  # masalan "uz", "ru" ... LANGUAGES kodlari bilan mos
    name: Mapped[str] = mapped_column(String(256))
    link: Mapped[str] = mapped_column(String(256))
    diamond_rank: Mapped[int] = mapped_column(Integer, default=0)  # katta bo'lsa - tepada chiqadi (reyting/olmos qiymati)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------------------
# PUL (Dollar) SOTIB OLISH NARXLARI
# ---------------------------------------------------------------------------
class MoneyPackage(Base):
    __tablename__ = "money_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    money_amount: Mapped[int] = mapped_column(BigInteger)     # nechta Dollar beriladi
    diamond_price: Mapped[int] = mapped_column(Integer)       # necha Olmosga sotiladi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------------------
# OLMOS SOTIB OLISH PAKETLARI (karta orqali, chek bilan tasdiqlanadi)
# ---------------------------------------------------------------------------
class DiamondPackage(Base):
    __tablename__ = "diamond_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price_sum: Mapped[int] = mapped_column(BigInteger)      # necha so'm / valyuta
    diamond_amount: Mapped[int] = mapped_column(Integer)    # nechta olmos beriladi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DiamondTopupRequest(Base):
    __tablename__ = "diamond_topup_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    package_id: Mapped[int] = mapped_column(ForeignKey("diamond_packages.id"))
    receipt_file_id: Mapped[str] = mapped_column(String(256))  # chek skrinshoti (telegram file_id)
    status: Mapped[DiamondRequestStatus] = mapped_column(
        SAEnum(DiamondRequestStatus), default=DiamondRequestStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# PARA (JUFTLIK) SO'ROVLARI
# ---------------------------------------------------------------------------
class PartnerRequest(Base):
    __tablename__ = "partner_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger)
    to_user_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/accepted/declined
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# ADMIN / UMUMIY SOZLAMALAR (key-value)
# ---------------------------------------------------------------------------
class BotSetting(Base):
    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class AdminUser(Base):
    __tablename__ = "admin_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# GURUH / O'YIN SESSIYASI
# ---------------------------------------------------------------------------
class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[GameStatus] = mapped_column(SAEnum(GameStatus), default=GameStatus.registration)
    day_number: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger)


class GamePlayer(Base):
    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    display_name: Mapped[str] = mapped_column(String(128))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    alive: Mapped[bool] = mapped_column(Boolean, default=True)
    is_inactive_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# MUKOFOT SOZLAMALARI (o'yin tugagach beriladigan pul/olmos)
# ---------------------------------------------------------------------------
class RewardSettings(Base):
    __tablename__ = "reward_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    winner_money: Mapped[int] = mapped_column(BigInteger, default=20)
    winner_diamond: Mapped[int] = mapped_column(Integer, default=0)
    loser_money: Mapped[int] = mapped_column(BigInteger, default=15)
    loser_diamond: Mapped[int] = mapped_column(Integer, default=0)
