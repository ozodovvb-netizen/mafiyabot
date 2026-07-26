"""
Ko'p tillilik (i18n) tizimi.

TEXTS lug'atida har bir kalit uchun 8 ta til (uz, ru, en, ar, id, kk, tr, ko) mavjud.
`t(key, lang, **kwargs)` orqali chaqiriladi, agar tarjima topilmasa "uz" ga qaytadi.

ESLATMA: uz/ru/en tillari to'liq tarjima qilingan. ar/id/kk/tr/ko tillarida
asosiy matnlar tarjima qilingan, lekin ba'zi uzun matnlar (masalan rol tavsiflari)
hozircha inglizcha bilan almashtirilgan - buni keyinchalik to'ldirishingiz mumkin.
"""

TEXTS: dict[str, dict[str, str]] = {

    "choose_language": {
        "uz": "Iltimos, tilni tanlang:",
        "ru": "Пожалуйста, выберите язык:",
        "en": "Please choose a language:",
        "ar": "الرجاء اختيار اللغة:",
        "id": "Silakan pilih bahasa:",
        "kk": "Тілді таңдаңыз:",
        "tr": "Lütfen bir dil seçin:",
        "ko": "언어를 선택해 주세요:",
    },

    "language_saved": {
        "uz": "✅ Til muvaffaqiyatli o'rnatildi!",
        "ru": "✅ Язык успешно установлен!",
        "en": "✅ Language set successfully!",
        "ar": "✅ تم ضبط اللغة بنجاح!",
        "id": "✅ Bahasa berhasil diatur!",
        "kk": "✅ Тіл сәтті орнатылды!",
        "tr": "✅ Dil başarıyla ayarlandı!",
        "ko": "✅ 언어가 설정되었습니다!",
    },

    "choose_gender": {
        "uz": "Jinsingizni tanlang:",
        "ru": "Выберите ваш пол:",
        "en": "Choose your gender:",
        "ar": "اختر جنسك:",
        "id": "Pilih jenis kelamin Anda:",
        "kk": "Жынысыңызды таңдаңыз:",
        "tr": "Cinsiyetinizi seçin:",
        "ko": "성별을 선택하세요:",
    },
    "gender_male": {
        "uz": "👦 Erkak", "ru": "👦 Мужской", "en": "👦 Male", "ar": "👦 ذكر",
        "id": "👦 Pria", "kk": "👦 Ер адам", "tr": "👦 Erkek", "ko": "👦 남성",
    },
    "gender_female": {
        "uz": "👧 Ayol", "ru": "👧 Женский", "en": "👧 Female", "ar": "👧 أنثى",
        "id": "👧 Wanita", "kk": "👧 Әйел адам", "tr": "👧 Kadın", "ko": "👧 여성",
    },

    "start_welcome": {
        "uz": (
            "Salom 👋\n"
            "Men mafiya botiman. Do'stlar bilan mafiya o'ynash uchun meni "
            "guruhingizga qo'shing va {max_players} kishilik o'yindan zavqlaning. "
            "Batafsil ma'lumot uchun\n\n"
            "👤 {admin_username}\n\n"
            "Meni admin qilib qo'yganingizdan so'ng, o'yinni boshlashingiz mumkin.."
        ),
        "ru": (
            "Привет 👋\n"
            "Я мафия-бот. Добавьте меня в свою группу, чтобы играть в мафию с друзьями "
            "и наслаждаться игрой до {max_players} человек. Подробнее:\n\n"
            "👤 {admin_username}\n\n"
            "После того как сделаете меня админом, вы сможете начать игру.."
        ),
        "en": (
            "Hello 👋\n"
            "I'm a Mafia bot. Add me to your group to play Mafia with friends "
            "and enjoy games with up to {max_players} players. For details:\n\n"
            "👤 {admin_username}\n\n"
            "After making me an admin, you can start the game.."
        ),
        "ar": "مرحباً 👋\nأنا بوت المافيا. أضفني إلى مجموعتك للعب مع الأصدقاء حتى {max_players} لاعب.\n\n👤 {admin_username}",
        "id": "Halo 👋\nSaya bot Mafia. Tambahkan saya ke grup Anda untuk bermain hingga {max_players} pemain.\n\n👤 {admin_username}",
        "kk": "Сәлем 👋\nМен мафия-ботпын. Достарыңызбен ойнау үшін мені топқа қосыңыз (макс {max_players} адам).\n\n👤 {admin_username}",
        "tr": "Merhaba 👋\nBen bir Mafya botuyum. Arkadaşlarınızla oynamak için beni grubunuza ekleyin (maks {max_players} kişi).\n\n👤 {admin_username}",
        "ko": "안녕하세요 👋\n저는 마피아 봇입니다. 친구들과 최대 {max_players}명까지 플레이하려면 그룹에 저를 추가하세요.\n\n👤 {admin_username}",
    },

    "btn_add_to_group": {
        "uz": "✅ Guruhga qo'shish", "ru": "✅ Добавить в группу", "en": "✅ Add to group",
        "ar": "✅ أضف إلى المجموعة", "id": "✅ Tambahkan ke grup", "kk": "✅ Топқа қосу",
        "tr": "✅ Gruba ekle", "ko": "✅ 그룹에 추가",
    },
    "btn_questions": {
        "uz": "✍️ Savollar uchun", "ru": "✍️ По вопросам", "en": "✍️ Questions",
        "ar": "✍️ للأسئلة", "id": "✍️ Pertanyaan", "kk": "✍️ Сұрақтар үшін",
        "tr": "✍️ Sorular için", "ko": "✍️ 문의사항",
    },
    "btn_premium_groups": {
        "uz": "💎 Premium guruhlar", "ru": "💎 Премиум группы", "en": "💎 Premium groups",
        "ar": "💎 مجموعات مميزة", "id": "💎 Grup premium", "kk": "💎 Премиум топтар",
        "tr": "💎 Premium gruplar", "ko": "💎 프리미엄 그룹",
    },
    "btn_back": {
        "uz": "↩️ Orqaga", "ru": "↩️ Назад", "en": "↩️ Back", "ar": "↩️ رجوع",
        "id": "↩️ Kembali", "kk": "↩️ Артқа", "tr": "↩️ Geri", "ko": "↩️ 뒤로",
    },
    "btn_change_language": {
        "uz": "🌐 Tilni o'zgartirish", "ru": "🌐 Изменить язык", "en": "🌐 Change language",
        "ar": "🌐 تغيير اللغة", "id": "🌐 Ubah bahasa", "kk": "🌐 Тілді өзгерту",
        "tr": "🌐 Dili değiştir", "ko": "🌐 언어 변경",
    },

    # --- Profil ---
    "profile_text": {
        "uz": (
            "{name}\n\n"
            "💵 Dollar: {money}\n"
            "💎 Olmos: {diamonds}\n\n"
            "🛡 Himoya: {himoya}\n"
            "📄 Hujjat: {hujjat}\n"
            "🪂 Osishdan himoya: {osishdan}\n"
            "🩸 Qotildan himoya: {qotildan}\n"
            "🌾 Miltiq: {miltiq}\n"
            "🧪 Doridan himoya: {doridan}\n"
            "🎭 Maska: {maska}\n"
            "🥷 Sirpanishdan himoya: {sirpanish}\n"
            "📗 Qahramon himoyasi: {qahramon}\n\n"
            "📊 Statistika:\n"
            "🎯 G'alabalar: {wins}\n"
            "🎮 Jami o'yinlar: {total_games}\n\n"
            "🎭 Faol rollar: {active_role}\n"
            "❤️ Sizning juftingiz: {partner}\n\n"
            "🎉 {news_channel} kanalga obuna bo'lsangiz yutuqdan 4x mukofot olasiz! "
            "VIP bo'lsangiz 10x!"
        ),
        "ru": (
            "{name}\n\n"
            "💵 Доллар: {money}\n"
            "💎 Алмаз: {diamonds}\n\n"
            "🛡 Защита: {himoya}\n"
            "📄 Документ: {hujjat}\n"
            "🪂 Защита от повешения: {osishdan}\n"
            "🩸 Защита от убийства: {qotildan}\n"
            "🌾 Ружьё: {miltiq}\n"
            "🧪 Защита от яда: {doridan}\n"
            "🎭 Маска: {maska}\n"
            "🥷 Защита от проверки: {sirpanish}\n"
            "📗 Защита героя: {qahramon}\n\n"
            "📊 Статистика:\n"
            "🎯 Победы: {wins}\n"
            "🎮 Всего игр: {total_games}\n\n"
            "🎭 Активная роль: {active_role}\n"
            "❤️ Ваш партнёр: {partner}\n\n"
            "🎉 Подпишитесь на {news_channel} и получите 4x награду за победу! VIP — 10x!"
        ),
        "en": (
            "{name}\n\n"
            "💵 Dollar: {money}\n"
            "💎 Diamonds: {diamonds}\n\n"
            "🛡 Protection: {himoya}\n"
            "📄 Document: {hujjat}\n"
            "🪂 Hanging protection: {osishdan}\n"
            "🩸 Kill protection: {qotildan}\n"
            "🌾 Rifle: {miltiq}\n"
            "🧪 Poison protection: {doridan}\n"
            "🎭 Mask: {maska}\n"
            "🥷 Check protection: {sirpanish}\n"
            "📗 Hero protection: {qahramon}\n\n"
            "📊 Statistics:\n"
            "🎯 Wins: {wins}\n"
            "🎮 Total games: {total_games}\n\n"
            "🎭 Active role: {active_role}\n"
            "❤️ Your partner: {partner}\n\n"
            "🎉 Subscribe to {news_channel} to get 4x reward on win! VIP gets 10x!"
        ),
    },
    "no_role": {
        "uz": "Yo'q", "ru": "Нет", "en": "None", "ar": "لا يوجد", "id": "Tidak ada",
        "kk": "Жоқ", "tr": "Yok", "ko": "없음",
    },
    "no_partner": {
        "uz": "Sizning juftingiz yo'q", "ru": "У вас нет партнёра", "en": "You have no partner",
        "ar": "ليس لديك شريك", "id": "Anda tidak punya pasangan", "kk": "Серіктесіңіз жоқ",
        "tr": "Partneriniz yok", "ko": "파트너가 없습니다",
    },

    "btn_shaxsiy_kabinet": {
        "uz": "🌐 Shaxsiy kabinet", "ru": "🌐 Личный кабинет", "en": "🌐 Personal cabinet",
        "ar": "🌐 الملف الشخصي", "id": "🌐 Kabinet pribadi", "kk": "🌐 Жеке кабинет",
        "tr": "🌐 Kişisel panel", "ko": "🌐 개인 페이지",
    },
    "btn_himoyalar": {
        "uz": "🛡 Himoyalar", "ru": "🛡 Защиты", "en": "🛡 Protections",
        "ar": "🛡 الحمايات", "id": "🛡 Perlindungan", "kk": "🛡 Қорғаныстар",
        "tr": "🛡 Korumalar", "ko": "🛡 보호",
    },
    "btn_para": {
        "uz": "💵 Para", "ru": "💵 Деньги", "en": "💵 Money", "ar": "💵 المال",
        "id": "💵 Uang", "kk": "💵 Ақша", "tr": "💵 Para", "ko": "💵 돈",
    },
    "btn_dokon": {
        "uz": "🛒 Do'kon", "ru": "🛒 Магазин", "en": "🛒 Shop", "ar": "🛒 المتجر",
        "id": "🛒 Toko", "kk": "🛒 Дүкен", "tr": "🛒 Mağaza", "ko": "🛒 상점",
    },
    "btn_xarid_qilish": {
        "uz": "🎯 Xarid qilish", "ru": "🎯 Покупка", "en": "🎯 Purchase",
        "ar": "🎯 شراء", "id": "🎯 Beli", "kk": "🎯 Сатып алу", "tr": "🎯 Satın al", "ko": "🎯 구매",
    },
    "btn_mening_geroyim": {
        "uz": "🦸 Mening geroyim", "ru": "🦸 Мой герой", "en": "🦸 My hero",
        "ar": "🦸 بطلي", "id": "🦸 Pahlawan saya", "kk": "🦸 Менің қаһарманым",
        "tr": "🦸 Kahramanım", "ko": "🦸 내 영웅",
    },

    # --- Himoyalar ---
    "protections_title": {
        "uz": "🛡 Himoyalarni yoqish yoki o'chirish:", "ru": "🛡 Включить или выключить защиты:",
        "en": "🛡 Turn protections on or off:", "ar": "🛡 تفعيل أو إيقاف الحمايات:",
        "id": "🛡 Aktifkan atau nonaktifkan perlindungan:", "kk": "🛡 Қорғанысты қосу немесе өшіру:",
        "tr": "🛡 Korumaları aç veya kapat:", "ko": "🛡 보호 기능 켜기/끄기:",
    },
    "on": {"uz": "ON", "ru": "ВКЛ", "en": "ON", "ar": "تشغيل", "id": "AKTIF", "kk": "ҚОСУЛЫ", "tr": "AÇIK", "ko": "켜짐"},
    "off": {"uz": "OFF", "ru": "ВЫКЛ", "en": "OFF", "ar": "إيقاف", "id": "NONAKTIF", "kk": "ӨШІРУЛІ", "tr": "KAPALI", "ko": "꺼짐"},
    "btn_faol_rol": {
        "uz": "🎭 Faol rol", "ru": "🎭 Активная роль", "en": "🎭 Active role",
        "ar": "🎭 الدور النشط", "id": "🎭 Peran aktif", "kk": "🎭 Белсенді рөл",
        "tr": "🎭 Aktif rol", "ko": "🎭 활성 역할",
    },

    # --- Para (Pul) ---
    "money_menu_title": {
        "uz": "Para menyu", "ru": "Меню денег", "en": "Money menu",
        "ar": "قائمة المال", "id": "Menu uang", "kk": "Ақша мәзірі", "tr": "Para menüsü", "ko": "돈 메뉴",
    },
    "no_money_yet": {
        "uz": "Sizda hali para yo'q. Random para topishingiz mumkin!\n\n🎲 Kuniga {limit} ta bepul so'rov beriladi.",
        "ru": "У вас пока нет денег. Вы можете найти случайные деньги!\n\n🎲 {limit} бесплатных попыток в день.",
        "en": "You have no money yet. You can find random money!\n\n🎲 {limit} free tries per day.",
        "ar": "ليس لديك مال بعد. يمكنك العثور على مال عشوائي!\n\n🎲 {limit} محاولات مجانية يومياً.",
        "id": "Anda belum punya uang. Anda bisa mencoba uang acak!\n\n🎲 {limit} percobaan gratis per hari.",
        "kk": "Сізде әлі ақша жоқ. Кездейсоқ ақша таба аласыз!\n\n🎲 Күніне {limit} тегін әрекет.",
        "tr": "Henüz paranız yok. Rastgele para bulabilirsiniz!\n\n🎲 Günde {limit} ücretsiz deneme.",
        "ko": "아직 돈이 없습니다. 무작위 돈을 찾아보세요!\n\n🎲 하루 {limit}회 무료 시도.",
    },
    "btn_random_money": {
        "uz": "🎲 Tasodifiy para topish", "ru": "🎲 Найти случайные деньги", "en": "🎲 Find random money",
        "ar": "🎲 العثور على مال عشوائي", "id": "🎲 Temukan uang acak", "kk": "🎲 Кездейсоқ ақша табу",
        "tr": "🎲 Rastgele para bul", "ko": "🎲 무작위 돈 찾기",
    },
    "btn_change_gender": {
        "uz": "🚻 Jinsni o'zgartirish ({used}/{limit})", "ru": "🚻 Сменить пол ({used}/{limit})",
        "en": "🚻 Change gender ({used}/{limit})", "ar": "🚻 تغيير الجنس ({used}/{limit})",
        "id": "🚻 Ubah jenis kelamin ({used}/{limit})", "kk": "🚻 Жынысты өзгерту ({used}/{limit})",
        "tr": "🚻 Cinsiyeti değiştir ({used}/{limit})", "ko": "🚻 성별 변경 ({used}/{limit})",
    },
    "btn_find_partner": {
        "uz": "💑 Para topish", "ru": "💑 Найти пару", "en": "💑 Find a partner",
        "ar": "💑 ابحث عن شريك", "id": "💑 Cari pasangan", "kk": "💑 Серіктес табу",
        "tr": "💑 Partner bul", "ko": "💑 파트너 찾기",
    },
    "gender_change_limit_reached": {
        "uz": "❌ Jinsni o'zgartirish limitingiz tugadi.", "ru": "❌ Ваш лимит смены пола исчерпан.",
        "en": "❌ Your gender change limit is over.", "ar": "❌ انتهى حد تغيير الجنس الخاص بك.",
        "id": "❌ Batas ubah jenis kelamin Anda habis.", "kk": "❌ Жынысты өзгерту лимитіңіз аяқталды.",
        "tr": "❌ Cinsiyet değiştirme limitiniz doldu.", "ko": "❌ 성별 변경 한도가 초과되었습니다.",
    },
    "random_money_result": {
        "uz": "🎉 Siz {amount} 💵 Dollar topdingiz!", "ru": "🎉 Вы нашли {amount} 💵!",
        "en": "🎉 You found {amount} 💵!", "ar": "🎉 لقد وجدت {amount} 💵!",
        "id": "🎉 Anda menemukan {amount} 💵!", "kk": "🎉 Сіз {amount} 💵 таптыңыз!",
        "tr": "🎉 {amount} 💵 buldunuz!", "ko": "🎉 {amount} 💵를 찾았습니다!",
    },
    "no_free_tries_left": {
        "uz": "❌ Bugungi bepul urinishlaringiz tugadi. Ertaga qayta urinib ko'ring.",
        "ru": "❌ Ваши бесплатные попытки на сегодня закончились. Попробуйте завтра.",
        "en": "❌ You've used all free tries for today. Try again tomorrow.",
        "ar": "❌ لقد استخدمت جميع محاولاتك المجانية اليوم. حاول مرة أخرى غداً.",
        "id": "❌ Anda telah menggunakan semua percobaan gratis hari ini. Coba lagi besok.",
        "kk": "❌ Бүгінгі тегін әрекеттеріңіз бітті. Ертең қайталап көріңіз.",
        "tr": "❌ Bugünkü ücretsiz denemeleriniz bitti. Yarın tekrar deneyin.",
        "ko": "❌ 오늘의 무료 시도를 모두 사용했습니다. 내일 다시 시도하세요.",
    },

    # --- Para taklifi (juftlik) ---
    "partner_ask_target": {
        "uz": "Kimga para bo'lish taklifini yubormoqchisiz? Foydalanuvchining ID raqamini yuboring:",
        "ru": "Кому вы хотите отправить предложение стать парой? Отправьте ID пользователя:",
        "en": "Who do you want to send a partner request to? Send the user's ID:",
        "ar": "لمن تريد إرسال طلب الشراكة؟ أرسل معرف المستخدم:",
        "id": "Kepada siapa Anda ingin mengirim permintaan pasangan? Kirim ID pengguna:",
        "kk": "Кімге серіктестік ұсынысын жібермекчісіз? Пайдаланушы ID сын жіберіңіз:",
        "tr": "Kime partnerlik teklifi göndermek istiyorsunuz? Kullanıcı ID'sini gönderin:",
        "ko": "누구에게 파트너 요청을 보내시겠습니까? 사용자 ID를 보내세요:",
    },
    "partner_request_sent_to_target": {
        "uz": "💌 Sizga {from_name} para bo'lish taklifini beryapti, qabul qilasizmi?",
        "ru": "💌 {from_name} предлагает вам стать парой, вы согласны?",
        "en": "💌 {from_name} is offering you to become a partner, do you accept?",
        "ar": "💌 {from_name} يقترح عليك أن تكونا شريكين، هل توافق؟",
        "id": "💌 {from_name} menawarkan Anda untuk menjadi pasangan, apakah Anda setuju?",
        "kk": "💌 {from_name} сізге серіктес болуды ұсынып жатыр, қабылдайсыз ба?",
        "tr": "💌 {from_name} size partner olmayı teklif ediyor, kabul ediyor musunuz?",
        "ko": "💌 {from_name}님이 파트너가 되기를 제안합니다. 수락하시겠습니까?",
    },
    "btn_yes": {"uz": "✅ Ha", "ru": "✅ Да", "en": "✅ Yes", "ar": "✅ نعم", "id": "✅ Ya", "kk": "✅ Иә", "tr": "✅ Evet", "ko": "✅ 예"},
    "btn_no": {"uz": "❌ Yo'q", "ru": "❌ Нет", "en": "❌ No", "ar": "❌ لا", "id": "❌ Tidak", "kk": "❌ Жоқ", "tr": "❌ Hayır", "ko": "❌ 아니요"},
    "partner_accepted_notify_sender": {
        "uz": "🎉 {to_name} para bo'lish taklifingizni qabul qildi!",
        "ru": "🎉 {to_name} принял(а) ваше предложение стать парой!",
        "en": "🎉 {to_name} accepted your partner request!",
    },
    "partner_declined_notify_sender": {
        "uz": "😔 {to_name} para bo'lish taklifingizni rad etdi.",
        "ru": "😔 {to_name} отклонил(а) ваше предложение.",
        "en": "😔 {to_name} declined your partner request.",
    },
    "partner_you_accepted": {
        "uz": "✅ Siz {from_name} taklifini qabul qildingiz!",
        "ru": "✅ Вы приняли предложение {from_name}!",
        "en": "✅ You accepted {from_name}'s request!",
    },
    "partner_you_declined": {
        "uz": "❌ Siz {from_name} taklifini rad etdingiz.",
        "ru": "❌ Вы отклонили предложение {from_name}.",
        "en": "❌ You declined {from_name}'s request.",
    },
    "searching_partner": {
        "uz": "🔎 Sizga mos para izlanmoqda...", "ru": "🔎 Ищем вам пару...", "en": "🔎 Looking for a partner for you...",
    },
    "no_candidates_found": {
        "uz": "😔 Hozircha mos foydalanuvchi topilmadi, birozdan so'ng qayta urinib ko'ring.",
        "ru": "😔 Подходящих пользователей пока нет, попробуйте позже.",
        "en": "😔 No suitable users found right now, try again later.",
    },

    # --- Do'kon ---
    "shop_title": {
        "uz": "🛒 Do'kon - nima sotib olamiz?", "ru": "🛒 Магазин - что купим?", "en": "🛒 Shop - what to buy?",
        "ar": "🛒 المتجر - ماذا نشتري؟", "id": "🛒 Toko - mau beli apa?", "kk": "🛒 Дүкен - не сатып аламыз?",
        "tr": "🛒 Mağaza - ne alalım?", "ko": "🛒 상점 - 무엇을 살까요?",
    },
    "shop_item_bought": {
        "uz": "✅ Siz {item_name} sotib oldingiz!", "ru": "✅ Вы купили {item_name}!", "en": "✅ You bought {item_name}!",
    },
    "not_enough_balance": {
        "uz": "❌ Balansingiz yetarli emas.", "ru": "❌ Недостаточно средств.", "en": "❌ Not enough balance.",
        "ar": "❌ رصيدك غير كافٍ.", "id": "❌ Saldo tidak cukup.", "kk": "❌ Балансыңыз жеткіліксіз.",
        "tr": "❌ Bakiyeniz yetersiz.", "ko": "❌ 잔액이 부족합니다.",
    },

    # --- Geroy ---
    "no_hero_yet": {
        "uz": "Sizda hali geroy yo'q.\n\nSiz Telegram Stars orqali yangi Geroy sotib olishingiz mumkin!",
        "ru": "У вас пока нет героя.\n\nВы можете купить нового героя через Telegram Stars!",
        "en": "You don't have a hero yet.\n\nYou can buy a new hero via Telegram Stars!",
    },
    "btn_buy_hero_diamond": {
        "uz": "🦸 Geroy sotib olish ({price} 💎)", "ru": "🦸 Купить героя ({price} 💎)", "en": "🦸 Buy hero ({price} 💎)",
    },
    "btn_buy_hero_stars": {
        "uz": "🦸 Geroy sotib olish ({price} ⭐)", "ru": "🦸 Купить героя ({price} ⭐)", "en": "🦸 Buy hero ({price} ⭐)",
    },
    "hero_bought": {
        "uz": "🎉 Tabriklaymiz! Siz {hero_name} geroysini sotib oldingiz!",
        "ru": "🎉 Поздравляем! Вы приобрели героя {hero_name}!",
        "en": "🎉 Congratulations! You bought the hero {hero_name}!",
    },

    # --- Premium guruhlar ---
    "premium_groups_title": {
        "uz": "Top 10 premium guruhlar:", "ru": "Топ 10 премиум групп:", "en": "Top 10 premium groups:",
        "ar": "أفضل 10 مجموعات مميزة:", "id": "Top 10 grup premium:", "kk": "Топ 10 премиум топтар:",
        "tr": "En iyi 10 premium grup:", "ko": "프리미엄 그룹 상위 10개:",
    },
    "no_premium_groups": {
        "uz": "Hozircha bu til/davlat uchun premium guruhlar mavjud emas.",
        "ru": "Пока нет премиум групп для этого языка/страны.",
        "en": "No premium groups available for this language/country yet.",
    },

    # --- Diamond (Olmos xarid) ---
    "diamond_menu_title": {
        "uz": "Qancha olmos sotib olmoqchisiz?\n\nTo'lovni amalga oshiring. To'lovdan so'ng chek skrinshotini yuboring, admin tasdiqlagach olmos hisobingizga qo'shiladi.",
        "ru": "Сколько алмазов хотите купить?\n\nСовершите оплату. После оплаты отправьте скриншот чека, после подтверждения администратором алмазы будут зачислены.",
        "en": "How many diamonds do you want to buy?\n\nMake the payment. After payment, send a screenshot of the receipt; diamonds will be added after admin approval.",
    },
    "diamond_send_receipt": {
        "uz": "💳 To'lov: {price} so'm → {diamonds} 💎\n\nKarta: {card_number}\n\nTo'lovni amalga oshirib, chek skrinshotini shu yerga yuboring 👇",
        "ru": "💳 Оплата: {price} сум → {diamonds} 💎\n\nКарта: {card_number}\n\nПосле оплаты отправьте скриншот чека сюда 👇",
        "en": "💳 Payment: {price} → {diamonds} 💎\n\nCard: {card_number}\n\nAfter payment, send the receipt screenshot here 👇",
    },
    "receipt_received": {
        "uz": "✅ Chekingiz qabul qilindi! Admin tasdiqlashini kuting ⏳",
        "ru": "✅ Ваш чек принят! Ожидайте подтверждения администратора ⏳",
        "en": "✅ Your receipt was received! Wait for admin approval ⏳",
    },
    "diamond_topup_approved_user": {
        "uz": "🎉 To'lovingiz tasdiqlandi! Hisobingizga {amount} 💎 qo'shildi.",
        "ru": "🎉 Ваш платёж подтверждён! На ваш счёт зачислено {amount} 💎.",
        "en": "🎉 Your payment was approved! {amount} 💎 has been added to your account.",
    },
    "diamond_topup_rejected_user": {
        "uz": "❌ Kechirasiz, to'lovingiz tasdiqlanmadi. Savollar bo'lsa admin bilan bog'laning.",
        "ru": "❌ К сожалению, ваш платёж не был подтверждён. По вопросам обратитесь к администратору.",
        "en": "❌ Sorry, your payment was not approved. Contact admin for questions.",
    },

    # --- Pul (Dollar) xarid ---
    "money_shop_title": {
        "uz": "💰 Olmos evaziga dollar xarid qilishingiz mumkin!",
        "ru": "💰 Вы можете купить доллары за алмазы!",
        "en": "💰 You can buy dollars using diamonds!",
    },
    "money_bought": {
        "uz": "✅ Siz {money} 💵 sotib oldingiz!", "ru": "✅ Вы купили {money} 💵!", "en": "✅ You bought {money} 💵!",
    },

    # --- Rollar ---
    "roles_list_title": {
        "uz": "Rollar ro'yhati:", "ru": "Список ролей:", "en": "Roles list:",
        "ar": "قائمة الأدوار:", "id": "Daftar peran:", "kk": "Рөлдер тізімі:",
        "tr": "Rol listesi:", "ko": "역할 목록:",
    },
    "role_detail": {
        "uz": "{emoji} <b>{name}</b>\n━━━━━━━━━━━━━━\n\n{description}",
        "ru": "{emoji} <b>{name}</b>\n━━━━━━━━━━━━━━\n\n{description}",
        "en": "{emoji} <b>{name}</b>\n━━━━━━━━━━━━━━\n\n{description}",
    },

    # --- Guruh o'yini: ro'yxatdan o'tish ---
    "group_registration_open": {
        "uz": (
            "🎮 <b>Ro'yxatdan o'tish boshlandi!</b>\n"
            "Kamida <b>{min_players}</b> kishi kerak.\n"
            "━━━━━━━━━━━━━━\n\n"
            "👥 <b>Ro'yhatdan o'tganlar ({count}):</b>\n{players_list}"
        ),
        "ru": (
            "🎮 <b>Регистрация началась!</b>\n"
            "Нужно минимум <b>{min_players}</b> человек.\n"
            "━━━━━━━━━━━━━━\n\n"
            "👥 <b>Зарегистрированные ({count}):</b>\n{players_list}"
        ),
        "en": (
            "🎮 <b>Registration started!</b>\n"
            "At least <b>{min_players}</b> players needed.\n"
            "━━━━━━━━━━━━━━\n\n"
            "👥 <b>Registered ({count}):</b>\n{players_list}"
        ),
    },
    "btn_join_game": {
        "uz": "🎮 Qo'shilish", "ru": "🎮 Присоединиться", "en": "🎮 Join",
        "ar": "🎮 انضم", "id": "🎮 Gabung", "kk": "🎮 Қосылу", "tr": "🎮 Katıl", "ko": "🎮 참가",
    },
    "joined_game_success": {
        "uz": "✅ Siz o'yinga omadli qo'shildingiz!", "ru": "✅ Вы успешно присоединились к игре!",
        "en": "✅ You've successfully joined the game!",
    },
    "btn_go_to_group": {
        "uz": "↩️ Guruhga o'tish", "ru": "↩️ Перейти в группу", "en": "↩️ Go to group",
    },
    "not_enough_players": {
        "uz": "❌ Yetarli o'yinchi yo'q. O'yin bekor qilindi.",
        "ru": "❌ Недостаточно игроков. Игра отменена.",
        "en": "❌ Not enough players. Game cancelled.",
    },

    # --- O'yin oqimi ---
    "game_started": {
        "uz": "🎮 O'yin boshlandi! (Rejim: {mode})", "ru": "🎮 Игра началась! (Режим: {mode})",
        "en": "🎮 Game started! (Mode: {mode})",
    },
    "night_started": {
        "uz": "🌙 {night_number}-tun boshlandi. Rollar o'z vazifasini bajarishlari mumkin.",
        "ru": "🌙 Наступила {night_number}-я ночь. Роли могут выполнять свои действия.",
        "en": "🌙 Night {night_number} has begun. Roles may act.",
    },
    "day_started": {
        "uz": "🌞 {day_number}-kun boshlandi.", "ru": "🌞 Начался {day_number}-й день.",
        "en": "🌞 Day {day_number} has begun.",
    },
    "voting_started": {
        "uz": "⚖️ Ovoz berish vaqti! ({seconds} soniya)", "ru": "⚖️ Время голосования! ({seconds} секунд)",
        "en": "⚖️ Voting time! ({seconds} seconds)",
    },
    "vote_recorded": {
        "uz": "{voter} - {target}ga ovoz berdi", "ru": "{voter} - проголосовал(а) за {target}",
        "en": "{voter} - voted for {target}",
    },
    "vote_result": {
        "uz": "Ovoz berish natijalari:\n{likes} 👍 | {dislikes} 👎",
        "ru": "Результаты голосования:\n{likes} 👍 | {dislikes} 👎",
        "en": "Voting results:\n{likes} 👍 | {dislikes} 👎",
    },
    "player_hanged": {
        "uz": "{name} kunduzgi yig'ilishda osildi! U edi {role_emoji} {role_name}.",
        "ru": "{name} был(а) повешен(а) на дневном собрании! Он(а) был(а) {role_emoji} {role_name}.",
        "en": "{name} was hanged at the day meeting! They were {role_emoji} {role_name}.",
    },
    "last_words_prompt_dm": {
        "uz": "💀 Siz o'yindan chetlatildingiz. Oxirgi so'zingizni shu yerga (botga) yozing — u guruhga e'lon qilinadi! ({seconds} soniya)",
        "ru": "💀 Вы выбыли из игры. Напишите свои последние слова сюда (боту) — они будут объявлены в группе! ({seconds} секунд)",
        "en": "💀 You've been eliminated. Write your last words here (to the bot) — they'll be announced in the group! ({seconds} seconds)",
    },
    "last_words_wait_group": {
        "uz": "💀 {name} chetlatildi va hozir botga oxirgi so'zini yozmoqda...",
        "ru": "💀 {name} выбыл(а) и сейчас пишет боту свои последние слова...",
        "en": "💀 {name} was eliminated and is now writing their last words to the bot...",
    },
    "last_words_announced": {
        "uz": "Aholidan kimdir {name} o'limidan oldin qichqirganini eshitgan:\n\"{words}\" - deb qichqirganini eshitgan.",
        "ru": "Кто-то из жителей услышал, как {name} перед смертью кричал(а):\n\"{words}\"",
        "en": "Someone among the residents heard {name} scream before dying:\n\"{words}\"",
    },
    "night_kill_announced": {
        "uz": "💀 Zombilardan biri kimnidir tishlab oldi!\n🎯 Xakker o'ljasini tanladi.",
        "ru": "💀 Один из зомби кого-то укусил!\n🎯 Хакер выбрал жертву.",
        "en": "💀 One of the zombies bit someone!\n🎯 Hacker chose a target.",
    },
    "trust_message": {
        "uz": "Ishonish qiyin! Lekin bu tunda hech kim o'lmadi...",
        "ru": "Трудно поверить! Но этой ночью никто не умер...",
        "en": "Hard to believe! But no one died this night...",
    },
    "inactive_warning": {
        "uz": "⚠️ {name} uzoq vaqtdan beri harakat qilmayapti. Agar {seconds} soniyada javob bermasa o'yindan chetlashtiriladi.",
        "ru": "⚠️ {name} долго не отвечает. Если не ответит за {seconds} секунд, будет удалён из игры.",
        "en": "⚠️ {name} has been inactive for a while. If no response in {seconds} seconds, they'll be removed.",
    },
    "player_removed_inactive": {
        "uz": "😴 {name} faolsizligi sababli o'yindan chetlashtirildi.",
        "ru": "😴 {name} удалён из игры за бездействие.",
        "en": "😴 {name} was removed from the game due to inactivity.",
    },

    "game_over_title": {
        "uz": "O'yin tugadi!", "ru": "Игра окончена!", "en": "Game over!",
    },
    "winners_title": {
        "uz": "G'oliblar:", "ru": "Победители:", "en": "Winners:",
    },
    "other_players_title": {
        "uz": "Qolgan o'yinchilar:", "ru": "Остальные игроки:", "en": "Other players:",
    },
    "game_duration": {
        "uz": "O'yin davomiyligi: {minutes} minut", "ru": "Длительность игры: {minutes} минут",
        "en": "Game duration: {minutes} minutes",
    },
    "reward_notice": {
        "uz": "🎁 G'oliblar mukofot oldi! {news_channel} kanali a'zosi: 4x, VIP: 10x",
        "ru": "🎁 Победители получили награду! Подписчики {news_channel}: 4x, VIP: 10x",
        "en": "🎁 Winners received rewards! {news_channel} subscribers: 4x, VIP: 10x",
    },
    "personal_result_won": {
        "uz": "🎉 O'yin tugadi.\nSizga {money} 💵, {diamonds} 💎 berildi!",
        "ru": "🎉 Игра окончена.\nВам начислено {money} 💵, {diamonds} 💎!",
        "en": "🎉 Game over.\nYou received {money} 💵, {diamonds} 💎!",
    },
}


def t(key: str, lang: str | None, **kwargs) -> str:
    """Berilgan kalit va til uchun matnni qaytaradi. Topilmasa uz/en ga qaytadi."""
    lang = lang or "uz"
    entry = TEXTS.get(key)
    if entry is None:
        return f"[[{key}]]"
    text = entry.get(lang) or entry.get("uz") or entry.get("en") or f"[[{key}]]"
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text
