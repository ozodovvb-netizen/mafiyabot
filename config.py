"""
Botning asosiy konfiguratsiyasi.
Barcha maxfiy ma'lumotlar (.env) faylidan o'qiladi.
"""
import os
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(raw_url: str) -> str:
    """
    Railway (va ko'pchilik hosting)lar DATABASE_URL ni odatda
    ``postgres://...`` yoki ``postgresql://...`` ko'rinishida beradi.
    Bizga esa asyncpg drayveri kerak: ``postgresql+asyncpg://...``.
    Bundan tashqari ``sslmode=require`` kabi psycopg2-uslubidagi
    query-parametrlarni asyncpg tushunmaydi, shuning uchun ularni
    tozalab, DATABASE_SSL orqali alohida boshqaramiz (db.py da).
    """
    if not raw_url:
        return raw_url

    # postgres:// yoki postgresql:// -> postgresql+asyncpg://
    raw_url = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", raw_url, count=1)

    parts = urlsplit(raw_url)
    if parts.scheme.startswith("postgresql") and "+asyncpg" not in parts.scheme:
        parts = parts._replace(scheme="postgresql+asyncpg")

    # asyncpg query-parametrlarni (masalan sslmode, sslrootcert) tushunmaydi -> olib tashlaymiz
    if parts.query:
        query_pairs = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in ("sslmode", "ssl")]
        parts = parts._replace(query=urlencode(query_pairs))

    return urlunsplit(parts)

# --- Bot sozlamalari ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# Botning o'zi ishlaydigan username (deep-link uchun, masalan https://t.me/Sherif_mafiabot)
BOT_USERNAME = os.getenv("BOT_USERNAME", "Sherif_mafiabot")

# --- Bosh adminlar (bot ishga tushganda avtomatik admin huquqiga ega bo'ladi) ---
# .env faylida: SUPER_ADMINS=123456789,987654321
SUPER_ADMINS = [
    int(x) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip().isdigit()
]

# --- PostgreSQL ulanish satri ---
# Railway/Render/Heroku kabi hostinglar odatda "postgres://" yoki "postgresql://"
# formatida beradi -- quyidagi funksiya buni avtomatik "postgresql+asyncpg://" ga o'giradi,
# shuning uchun Railway'dan nusxalagan DATABASE_URL ni o'zgartirmasdan qo'yavering.
DATABASE_URL = _normalize_database_url(
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://mafia_user:mafia_pass@localhost:5432/mafia_bot",
    )
)

# Railway'ning tashqi (public) ulanishida ko'pincha SSL talab qilinadi.
# .env da DATABASE_SSL=true qo'ysangiz, asyncpg SSL bilan ulanadi.
DATABASE_SSL = os.getenv("DATABASE_SSL", "false").strip().lower() in ("1", "true", "yes")

# --- O'yin sozlamalari ---
MIN_PLAYERS = int(os.getenv("MIN_PLAYERS", "5"))
MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", "45"))

REGISTRATION_SECONDS = int(os.getenv("REGISTRATION_SECONDS", "90"))
NIGHT_SECONDS = int(os.getenv("NIGHT_SECONDS", "40"))
DAY_DISCUSSION_SECONDS = int(os.getenv("DAY_DISCUSSION_SECONDS", "60"))
VOTING_SECONDS = int(os.getenv("VOTING_SECONDS", "30"))
LAST_WORDS_SECONDS = int(os.getenv("LAST_WORDS_SECONDS", "30"))

# Kuniga nechta bepul "tasodifiy pul" so'rovi mumkin
FREE_MONEY_DAILY_LIMIT = int(os.getenv("FREE_MONEY_DAILY_LIMIT", "3"))

# Jinsni o'zgartirish limiti (umumiy, foydalanuvchi hisobida saqlanadi)
GENDER_CHANGE_LIMIT = int(os.getenv("GENDER_CHANGE_LIMIT", "3"))

# --- Qo'llab-quvvatlanadigan tillar ---
# Kod: (bayroq, nom) - tartib shu yerda ko'rsatilganidek chiqadi
LANGUAGES = {
    "uz": ("🇺🇿", "O'zbekcha"),
    "ru": ("🇷🇺", "Русский"),
    "en": ("🇺🇸", "English"),
    "ar": ("🇸🇦", "العربية"),
    "id": ("🇮🇩", "Indonesia"),
    "kk": ("🇰🇿", "Қазақша"),
    "tr": ("🇹🇷", "Türkçe"),
    "ko": ("🇰🇷", "한국어"),
}
DEFAULT_LANGUAGE = "uz"

# Faylni saqlash uchun papka (chek skrinshotlari, va h.k.)
MEDIA_STORAGE_CHANNEL_ID = int(os.getenv("MEDIA_STORAGE_CHANNEL_ID", "0"))  # ixtiyoriy
