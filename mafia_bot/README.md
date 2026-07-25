# 🕵️ Sherif Mafia — Telegram Mafiya Boti

Aiogram 3 + PostgreSQL asosida qurilgan, to'liq sozlanadigan (admin panel orqali) Mafiya bot.

## 📦 O'rnatish

```bash
# 1. Repo/papkani serverga yuklang, keyin:
cd mafia_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. PostgreSQL o'rnating va baza yarating:
sudo -u postgres psql
CREATE DATABASE mafia_bot;
CREATE USER mafia_user WITH PASSWORD 'mafia_pass';
GRANT ALL PRIVILEGES ON DATABASE mafia_bot TO mafia_user;
\q

# 3. .env faylini sozlang
cp .env.example .env
nano .env   # BOT_TOKEN, SUPER_ADMINS, DATABASE_URL ni to'ldiring

# 4. Botni ishga tushiring
python3 main.py
```

Birinchi ishga tushganda barcha jadvallar avtomatik yaratiladi (`init_db()`).

## 🛠 Ishga tushirgandan keyin - MAJBURIY sozlash tartibi

Bot ishga tushgach, **hech narsa sozlanmagan** holda keladi (rollar, do'kon, narxlar - bo'sh).
`.env` dagi `SUPER_ADMINS` ro'yxatidagi ID bilan botga `/admin` yuboring va tartib bilan quyidagilarni to'ldiring:

1. **🎭 Rollar** — kamida bir nechta rol qo'shing (masalan: Mafiya - kill, Doktor - heal,
   Komissar - check, Tinch aholi - none). Rol qo'shmasangiz o'yin boshlanmaydi!
2. **🛒 Do'kon** — himoya buyumlari (narxi, nimadan himoya qilishi)
3. **🦸 Geroylar** — (ixtiyoriy) geroy narxi va imkoniyatlari
4. **💎 Premium guruhlar** — har bir til/davlat uchun alohida
5. **💵 Pul narxlari** — Olmos evaziga Dollar narxlari
6. **💎 Olmos paketlari** — Karta orqali sotib olish narxlari
7. **👤 Admin username** — "Savollar uchun" tugmasida ko'rinadigan username
8. **💳 Karta raqami** — Olmos to'lovi uchun ko'rsatiladigan karta
9. **🏆 Mukofot sozlamalari** — g'olib/yutqazgan qancha pul/olmos olishi

Admin panelning **hamma bo'limi qo'shish/o'chirish (CRUD)** tarzida ishlaydi — istalgan vaqtda
yangi rol, buyum, geroy, guruh yoki narx qo'shishingiz, keraksizini o'chirishingiz mumkin.
Yangi narsa qo'shish kerak bo'lib qolsa, tegishli bo'limga o'xshash boshqa CRUD blokini
(masalan `handlers/admin/shop_admin.py` naqshi bo'yicha) qo'shishingiz mumkin.

## 🎮 Guruhda ishlatish

1. Botni guruhga qo'shing va **admin** qiling.
2. Guruhda `/game` yozing — ro'yxatdan o'tish boshlanadi.
3. O'yinchilar "🎮 Qo'shilish" tugmasi orqali botga o'tib ro'yxatdan o'tadi.
4. `REGISTRATION_SECONDS` (standart 90 soniya) o'tgach, agar `MIN_PLAYERS` yetsa, o'yin
   avtomatik boshlanadi: har biriga shaxsiy xabarda roli yuboriladi, keyin tun/kun/ovoz berish
   tsikli ishga tushadi.
5. `/stop` — o'yinni majburan to'xtatadi (host yoki guruh admini).
6. `/roles` — barcha rollar ro'yxati va tavsifi (istalgan joyda ishlaydi).

## 📁 Loyiha tuzilishi

```
mafia_bot/
├── main.py                  # Botni ishga tushiruvchi fayl
├── config.py                 # Barcha sozlamalar (.env dan o'qiydi)
├── database/
│   ├── models.py              # SQLAlchemy jadvallari
│   ├── db.py                  # Baza ulanishi
│   └── crud.py                # Barcha DB amallari
├── locales/texts.py           # 8 tilli matnlar (i18n)
├── keyboards/                 # Inline klaviaturalar
├── states/states.py           # FSM holatlari
├── game/
│   ├── engine.py               # O'yin dvigateli (tun/kun/ovoz/g'alaba)
│   └── roles_logic.py          # Rol taqsimlash va g'alaba sharti
└── handlers/
    ├── user/                   # Shaxsiy chat: start, profil, do'kon, himoyalar...
    ├── admin/                  # Admin panel: rollar, do'kon, geroylar, narxlar...
    └── group/                  # Guruh: /game, ro'yxatdan o'tish, tungi/kunduzgi harakatlar
```

## ⚠️ Muhim eslatmalar / kengaytirish kerak bo'lgan joylar

- **Til soni**: hozircha 8 ta til ulangan (`config.py` dagi `LANGUAGES`). Screenshotlarda 13 tagacha
  til ko'rsatilgan edi — agar kerak bo'lsa, `LANGUAGES` ga qo'shib, `locales/texts.py` dagi har bir
  kalitga shu til kodini qo'shishingiz kifoya.
- **Tarjimalar**: `uz`, `ru`, `en` to'liq tarjima qilingan. `ar`, `id`, `kk`, `tr`, `ko` uchun asosiy
  tugma/xabar matnlari tarjima qilingan, ammo ba'zi uzun matnlar hozircha o'zbekcha/inglizcha bilan
  almashtirilgan bo'lishi mumkin — `TEXTS` lug'atiga to'ldirib boring.
- **Kunduzgi nominatsiya**: hozirgi versiyada kun bosqichida shubhali odam **tasodifiy** tanlanadi
  (demo sifatida), chunki "guruh a'zolari kimni nomlashi" real vaqtli matn buyruqlari orqali
  yig'ilishi kerak. Buni to'liqlashtirish uchun `game/engine.py` dagi `run_day_phase()` ichida
  nominatsiya tugmalari qo'shib, eng ko'p ovoz olgan odamni tanlashingiz kerak bo'ladi.
- **Faolsizlarni chetlatish**: `inactive_warning` / `player_removed_inactive` matnlari tayyor,
  lekin to'liq avtomatik "necha marta javob bermasa chetlatiladi" hisoblagichi hozircha
  qo'shilmagan — `game/engine.py` da har bir harakat bosqichida oddiy counter qo'shish kifoya.
  qulaylik uchun asos (LAST_WORDS_LISTENERS kabi) allaqachon tayyor.
  qo'shilmagan.
- **Custom rollar**: admin panelda "Faqat matn (avtomatikasiz)" tanlangan rollar avtomatik
  tunda harakat qilmaydi — faqat jamoasi (mafiya/tinch/yakka) g'alaba hisobiga kiradi. Agar ular
  uchun ham maxsus mexanika kerak bo'lsa, `NightActionType` ga yangi turlar qo'shib,
  `game/engine.py` dagi `_resolve_night_actions()` ni kengaytirishingiz kerak.
- **Telegram Stars orqali geroy sotib olish**: `hero.py` da haqiqiy invoys yuborish kodi bor
  (ishlaydi), lekin buni test qilish uchun botni real ishga tushirib ko'rish kerak.
- **Guruhga qaytish tugmasi**: `https://t.me/c/...` linki faqat superguruh (supergroup)larda
  to'g'ri ishlaydi; oddiy guruh uchun Telegram username asosidagi link talab qilinadi.

## 🚂 Railway'ga deploy qilish

1. Repo'ni GitHub'ga yuklang, so'ng Railway'da **New Project → Deploy from GitHub repo**.
2. Xuddi shu loyihaga **PostgreSQL** plagin/servisini qo'shing (**New → Database → PostgreSQL**).
3. Bot servisining **Variables** bo'limiga quyidagilarni qo'shing:
   - `BOT_TOKEN` — BotFather'dan olingan token
   - `SUPER_ADMINS` — sizning Telegram ID'ingiz (vergul bilan bir nechtasi mumkin)
   - `DATABASE_URL` — agar bot va Postgres bitta Railway loyihasida bo'lsa, referens sifatida
     `${{Postgres.DATABASE_URL}}` deb yozing (Railway o'zi ichki host bilan almashtiradi — bu eng
     tez va ishonchli usul). Agar Postgres boshqa joyda bo'lsa, uning **Public Network** URL'ini
     to'liq nusxalab qo'ying — `postgres://` yoki `postgresql://` bo'lsa ham bot avtomatik
     `postgresql+asyncpg://` ga o'giradi.
4. **Settings → Deploy** bo'limida start buyrug'i avtomatik `Procfile`dagi `worker: python main.py`
   dan olinadi. Bu bot **worker** turida ishlaydi — HTTP portga chiqish/public domain shart emas,
   shuning uchun Railway'da "Generate Domain" qilish kerak emas.
5. Deploy tugagach, loglarda `Baza tayyor. Bot ishga tushmoqda...` chiqsa — ulanish muvaffaqiyatli.
   Agar ulanish xatosi chiqsa, to'liq xatolik matnini tekshiring — `db.py` endi sababini aniq
   log qiladi (masalan noto'g'ri parol, host topilmadi, va h.k.).

## 🔑 Kutubxonalar

```
aiogram==3.15.0
SQLAlchemy==2.0.36
asyncpg==0.30.0
python-dotenv==1.0.1
```

Barcha kod sintaksis va import jihatidan tekshirilgan (`py_compile` + real import test o'tkazilgan).
