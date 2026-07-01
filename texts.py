from datetime import datetime, timezone, timedelta

TASHKENT_TZ = timezone(timedelta(hours=5))

def time_greeting():
    h = datetime.now(TASHKENT_TZ).hour
    if 6 <= h < 11:   return "🌅 Ohayo! Yangi kun — yangi sarguzasht!"
    elif 11 <= h < 18: return "☀️ Konnichiwa~ Kunduzgi tanaffusda ham anime?"
    elif 18 <= h < 23: return "🌆 Konbanwa~ Kechki choy bilan anime — zo'r kombinatsiya!"
    else:              return "🌙 Oyasumi oldidan oxirgi bir qism?"

def address(gender):
    return "Senpai" if gender == "senpai" else ("Hime-chan" if gender == "hime" else "do'stim")

# ── FOYDALANUVCHI ──
WELCOME_INTRO = (
    "⛩️ <i>...Sakura gullari orasidan bir nur tushdi...</i>\n\n"
    "🌸 <b>Yuki:</b> Salom! Men seni kutib turardim.\n"
    "Xush kelibsan <b>Sakura Olamiga</b> ✨"
)

SUBSCRIBE_REQUEST = (
    "🔒 Bu olam maxsus. Kirish uchun quyidagi\n"
    "<b>Torii darvozalaridan</b> o'tib kel 👇"
)
SUBSCRIBE_CHECK_BTN = "✅ Tekshirish"
SUBSCRIBE_FAIL = "Hali barcha kanallarga obuna bo'lmading. Iltimos tekshirib qayta ur 🙏"
SUBSCRIBE_SUCCESS = "✅ Ajoyib! Endi sen Sakura Olamining bir qismisan 🌸"

ASK_GENDER = "Senga qanday murojaat qilsam yaxshi? 👇"
GENDER_SENPAI_BTN = "🗡️ Senpai (Erkak)"
GENDER_HIME_BTN = "🌷 Hime-chan (Ayol)"
GENDER_REPLY_SENPAI = "🗡️ Senpai, xush kelibsan! Men senga eng zo'r sarguzashtlarni topib beraman ✨"
GENDER_REPLY_HIME = "🌷 Hime-chan, xush kelibsan! Bugun senga ajoyib anime topib beraman ✨"

# ── MENYU ──
MENU_SEARCH   = "🔍 Qidirish"
MENU_TOP      = "🏆 Top animelar"
MENU_HISTORY  = "📜 Tarixim"
MENU_FEEDBACK = "✉️ Murojaat"
MENU_ADS      = "📢 Reklama"
MENU_PREMIUM  = "💎 Premium"

# ── ANIME ──
ANIME_NOT_FOUND = "😔 Bunday anime topilmadi. Nom yoki kodni tekshirib qayta kiriting."
ANIME_FOUND     = "🎬 <b>{title}</b>\n📺 Jami: <b>{count} qism</b>"
CONTINUE_WATCHING = "▶️ <b>{title}</b> — {ep}-qismda to'xtagansan. Davom etamizmi?"
NO_HISTORY    = "📜 Hali hech narsa ko'rmagan ekansiz. Qidiruvdan boshlang!"
NO_TOP        = "Hali animelar yo'q. Tez orada paydo bo'ladi 🌸"
TOP_TITLE     = "🏆 <b>Eng ko'p ko'rilganlar:</b>\n\n"
LOADING       = "⏳ Qidirilmoqda..."
RATE_THANKS   = "Fikring uchun rahmat!"

EPISODE_CAPTION = "🎬 <b>{title}</b> — {ep}/{total} qism\n\n✨ Yoqimli tomosha, {addr}!"

# Tugmalar
PREV_BTN        = "⬅️ Oldingi"
NEXT_BTN        = "Keyingi ➡️"
ALL_EPISODES_BTN = "📋 Barcha qismlar"
LIKE_BTN        = "👍"
DISLIKE_BTN     = "👎"
SHARE_BTN       = "📤 Ulashish"
BACK_BTN        = "🔙 Orqaga"
FINISH_BTN      = "✅ Tugatish"
CANCEL_BTN      = "❌ Bekor qilish"

# ── FEEDBACK ──
FEEDBACK_ASK    = "✉️ Taklif yoki shikoyatingni yoz, {addr}. O'qiyman 💌"
FEEDBACK_THANKS = "💌 Maktubingni oldim, {addr}! Tez orada ko'rib chiqiladi."

# ── REKLAMA ──
ADS_TEXT = (
    "📢 <b>Reklama joylash</b>\n\n"
    "Botimizda reklama joylashtirmoqchimisiz?\n"
    "Admin bilan bog'laning 👇"
)

# ── PREMIUM ──
PREMIUM_TEXT = (
    "💎 <b>PREMIUM obuna</b>\n\n"
    "Premium afzalliklari:\n"
    "▫️ Majburiy obunasiz kirish\n"
    "▫️ Reklamasiz toza tajriba\n"
    "▫️ Sifatli formatda yuklash\n"
    "▫️ Eksklyuziv animelar\n\n"
    "📌 <b>Narxlar:</b>\n"
    "1 oy — <b>25 000 so'm</b>\n"
    "3 oy — <b>60 000 so'm</b>\n"
    "6 oy — <b>110 000 so'm</b>\n\n"
    "To'lov uchun admin bilan bog'laning 👇"
)
PREMIUM_BTN_1 = "1 oy — 25 000 so'm"
PREMIUM_BTN_3 = "3 oy — 60 000 so'm"
PREMIUM_BTN_6 = "6 oy — 110 000 so'm"
PREMIUM_REQUEST_SENT = "✅ So'rovingiz adminga yuborildi! Tez orada javob olasiz."

# ── ADMIN ──
NOT_ADMIN = "⛔️ Bu buyruq faqat adminlar uchun."

ADMIN_WELCOME = (
    "⛩️ <b>Admin paneli</b> — Okaerinasai, Yaratuvchi-sama!\n\n"
    "📊 Bugungi holat:\n"
    "👥 Jami: <b>{users}</b> ta | Bugun: <b>+{today}</b>\n"
    "💎 Premium: <b>{premium}</b> ta\n"
    "🎬 Animelar: <b>{anime}</b> ta | Qismlar: <b>{episodes}</b> ta"
)

ADMIN_MENU_ADD      = "🎬 Yangi anime"
ADMIN_MENU_ADD_EP   = "➕ Qism qo'shish"
ADMIN_MENU_LIST     = "📋 Anime ro'yxati"
ADMIN_MENU_CHANNELS = "⛩️ Kanallar"
ADMIN_MENU_BROADCAST= "📢 Xabar yuborish"
ADMIN_MENU_FEEDBACK = "✉️ Murojaatlar"
ADMIN_MENU_STATS    = "📊 Statistika"
ADMIN_MENU_PREMIUM  = "💎 Premium so'rovlar"
ADMIN_MENU_USER_MODE = "👤 Foydalanuvchi rejimi"
ADMIN_MENU_ADMINS   = "🛡 Adminlar"

NOT_SUPER_ADMIN = "⛔️ Bu buyruq faqat bosh adminlar (.env dagi) uchun."
ASK_ADD_ADMIN_ID = "🆔 Yangi admin qilmoqchi bo'lgan foydalanuvchi ID sini yuboring:"
ASK_REMOVE_ADMIN_ID = "🆔 Adminlikdan olib tashlamoqchi bo'lgan foydalanuvchi ID sini yuboring:"
ADMIN_ADDED = "✅ {uid} endi admin!"
ADMIN_ALREADY = "⚠️ {uid} allaqachon admin."
ADMIN_REMOVED = "✅ {uid} adminlikdan olindi."
ADMIN_NOT_FOUND_TO_REMOVE = "⚠️ {uid} bazadagi (dinamik) adminlar orasida topilmadi.\n(.env dagi bosh adminlarni bu yerdan o'chirib bo'lmaydi.)"

ASK_DESCRIPTION = "📝 Anime uchun qisqacha tavsif yozing (yoki o'tkazib yuborish uchun ➡️ Skip bosing):"
ASK_COVER = "🖼 Anime uchun muqova (rasm) yuboring (yoki o'tkazib yuborish uchun ➡️ Skip bosing):"
SKIP_BTN = "➡️ Skip"
DESCRIPTION_SAVED = "✅ Tavsif saqlandi."
COVER_SAVED = "✅ Muqova saqlandi."

ASK_NEW_TITLE     = "📝 Anime nomini yozing:"
NEW_ANIME_CREATED = (
    "✅ <b>{title}</b> yaratildi!\n"
    "🔢 Kod: <code>{code}</code>\n\n"
    "Endi videolarni ketma-ket <b>forward</b> qiling.\n"
    "Tugatgach ✅ Tugatish bosing."
)
EPISODE_ADDED   = "✅ {num}-qism qo'shildi! Yana forward qiling yoki tugatish bosing."
ADDING_FINISHED = "🎊 <b>{title}</b> — jami <b>{count}</b> ta qism saqlandi!"

ASK_ANIME_CODE_FOR_EP  = "🔢 Qaysi animega qism qo'shmoqchisiz? Kodni yuboring:"
ANIME_FOUND_FOR_EP     = "✅ <b>{title}</b> ({count} ta qism bor)\nEndi yangi qismlarni forward qiling:"

ASK_CHANNEL_ID    = "📌 Kanal username yoki ID yuboring:\nMasalan: <code>@kanal</code> yoki <code>-100123456</code>\n\n⚠️ Bot o'sha kanalda <b>admin</b> bo'lishi shart!"
ASK_CHANNEL_TITLE = "📝 Kanal nomi (foydalanuvchiga ko'rinadigan):"
ASK_CHANNEL_URL   = "🔗 Kanal havolasi (https://t.me/...):"
CHANNEL_ADDED     = "✅ Kanal qo'shildi!"

ASK_BROADCAST_TEXT = "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:"
BROADCAST_STARTED  = "🚀 Yuborish boshlandi..."
BROADCAST_DONE     = "✅ Tugadi! {success} ta yetdi, {fail} ta xato (shundan {blocked} tasi botni bloklagani uchun endi ro'yxatdan avtomatik chiqarildi)."

STATS_TEXT = (
    "📊 <b>To'liq statistika</b>\n\n"
    "👥 Jami: {users} | Bugun: +{today}\n"
    "💎 Premium: {premium}\n"
    "🎬 Animelar: {anime} | Qismlar: {episodes}\n"
    "👍 {likes} | 👎 {dislikes}\n"
    "✉️ Murojaatlar: {feedback}\n"
    "⛩️ Obuna: {sub_status} ({channels} ta)\n\n"
    "🏆 <b>Top-5:</b>\n{top_list}"
)
