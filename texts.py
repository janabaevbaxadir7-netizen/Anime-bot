# -*- coding: utf-8 -*-
"""
🌸 Yuki-chan — barcha xabar matnlari shu yerda jamlangan
(Kelajakda matnlarni o'zgartirish kerak bo'lsa, faqat shu faylni tahrirlang)
"""
from datetime import datetime, timezone, timedelta

TASHKENT_TZ = timezone(timedelta(hours=5))


def time_greeting() -> str:
    hour = datetime.now(TASHKENT_TZ).hour
    if 6 <= hour < 11:
        return "🌅 Ohayo gozaimasu!! ☀️💫 Yangi kun boshlandi, yuragim allaqachon hayajonda — bugun qanday sarguzasht kutyapti seni?! 🍥"
    elif 11 <= hour < 18:
        return "☀️ Konnichiwa~ 🌸 Kunduzgi tanaffusda meni sog'inmadingmi?! Kel, birga ajoyib anime topamiz! ✨"
    elif 18 <= hour < 23:
        return "🌆 Konbanwa, qadrdonim~ 🍵🌸 Kechki choy va anime — bundan zo'r narsa bormi?! 💕"
    else:
        return "🌙 Oyasumi oldidan... ✨ faqat bitta qism, va'da, faqat bitta! 😴💫 (lekin uxlashni unutma, meni xavotirga solma 🥺)"


WELCOME_INTRO = (
    "⛩️✨💫 <i>...Uzoq osmonlar ortidan kichkina bir nur yarqirab tushdi...</i>\n\n"
    "🌸 <b>Yuki-chan:</b> Kyaa~ konnichiwa!! 🥰 Men seni juda uzoq kutdim, bilasanmi?! "
    "Nihoyat keldingmi?! Yuragim taraqlab ketyapti hayajondan! 💓✨\n\n"
    "Sen hozir mening sehrli <b>Sakura Olamimga</b> qadam qo'yding 🍥🌸"
)

SUBSCRIBE_REQUEST = (
    "Lekin, lekin... 😳 bu olam juda nozik, uni faqat ishonchli do'stlarimgina bilishi mumkin...\n\n"
    "Iltimos, avval ⛩️ <b>Torii darvozalaridan</b> o'tib kel, keyin sen bilan to'liq sirlarimni "
    "baham ko'raman! 🙏💕"
)

SUBSCRIBE_CHECK_BTN = "✅ Tekshirish"

SUBSCRIBE_FAIL = (
    "😢 Eh-eh... Senpai, hali hamma Torii darvozalaridan o'tib bo'lmading shekilli...\n"
    "Iltimos, yuqoridagi barchasiga obuna bo'lib, keyin yana ✅ tugmasini bos! 🙏"
)

SUBSCRIBE_SUCCESS = "🎉✨ Yashashing! Endi sen rasman mening olamimning bir bo'lagisan! 🌸"

ASK_GENDER = (
    "Aaa, kechirasan, hayajonimdan so'rashni unutibman! 😅💫\n"
    "Senga qanday deb chaqirsam yuragingga yaqin bo'ladi? Aytsang-chi! 👉👈"
)

GENDER_SENPAI_BTN = "🗡️ Senpai"
GENDER_HIME_BTN = "🌷 Hime-chan"

GENDER_REPLY_SENPAI = (
    "Waaa, Senpai ekansan-ku!! 🗡️✨ Juda quvondim! Endi sen mening yo'l-boshchim bo'lasan, "
    "men esa senga eng zo'r sarguzashtlarni topib beraman, va'da! 🔥💫"
)
GENDER_REPLY_HIME = (
    "Kyaaa, Hime-chan, naqadar shirinsan! 🌷💖 Bugun senga eng zo'r sarguzashtni topib beraman, "
    "ko'rasan! ✨"
)


def address(gender: str) -> str:
    return "Senpai" if gender == "senpai" else ("Hime-chan" if gender == "hime" else "do'stim")


# ───────── Asosiy menyu ─────────
MENU_SEARCH = "⛩️ Anime izlash"
MENU_TOP = "🎴 Top animelar"
MENU_HISTORY = "📜 Mening yo'lim"
MENU_FEEDBACK = "✉️ Yuki-changa maktub"
MENU_ADS = "📢 E'lon taxtasi"

ASK_CODE = "🔍 Kodni yuboring (faqat raqam, masalan: <code>106</code>) 🌸"
ASK_CODE_INVALID = "😅 Gomen, Senpai... kod faqat raqamlardan iborat bo'lishi kerak! Masalan: <code>106</code>"

ANIME_NOT_FOUND = "😢 Gomen nasai... bunday kod bilan hech narsa topilmadi. Kodni tekshirib qayta yuboring 🙏"

ANIME_FOUND = "🎴✨ Kyaaa, topdim, topdim!! 🥳💕 Mana — <b>{title}</b>, jami {count} ta sarguzasht bor!"

CONTINUE_WATCHING = "👀 Senpai, sen <b>{title}</b> ning {ep}-qismida to'xtagan eding! Davom etamizmi? ▶️"

NO_HISTORY = "📜 Hali hech qanday sarguzasht boshlamagansan... ⛩️ Anime izlash orqali boshla! 🌸"

LOADING = "⏳✨ Yuki-chan sehr qilyapti, biroz kuting..."

EPISODE_CAPTION = "🎬 {title} — {ep}-qism\n\n✨ Yoqimli tomosha, {addr}! 🍥"

FEEDBACK_ASK = "✉️ Menga nima demoqchisan, {addr}? Taklif yoki shikoyatingni shu yerga yoz, men albatta o'qiyman! 💌"
FEEDBACK_THANKS = "💕 Rahmat, {addr}! Xabaringni Yaratuvchi-samaga yetkazdim! ✨"

ADS_TEXT = (
    "📢 <b>E'lon taxtasi</b>\n\n"
    "Bu yerda reklama joylashtirishni xohlaysizmi? 🌸\n"
    "Admin bilan bog'lanish uchun pastdagi tugmani bosing! 💌"
)

NO_TOP = "🎴 Hali animelar yo'q ekan... tez orada paydo bo'ladi! 🌸"
TOP_TITLE = "🔥✨ Eng sevimli sarguzashtlar:\n\n"

WATCH_BTN = "▶️ Tomosha qilish"
SHARE_BTN = "📤 Do'stga ulashish"
LIKE_BTN = "👍"
DISLIKE_BTN = "👎"
PREV_BTN = "⬅️ Oldingi"
NEXT_BTN = "Keyingi ➡️"
ALL_EPISODES_BTN = "📋 Barcha qismlar"
BACK_BTN = "🔙 Orqaga"

RATE_THANKS = "💕 Fikring uchun rahmat!"


# ───────── ADMIN ─────────
ADMIN_WELCOME = (
    "⛩️🔥💫 <i>Okaerinasai, Yaratuvchi-sama!!!</i> 🙇‍♀️✨\n"
    "Sizni ko'rganimdan juda xursandman! Kelgan vaqtingizda olam ham yorishib ketadi!\n\n"
    "📊 <b>Bugungi holat:</b>\n"
    "👥 Jami sayohatchilar: {users}\n"
    "📈 Bugun: +{today} yangi do'st keldi! 🎉\n"
    "🎴 Jami sarguzashtlar: {anime} | Qismlar: {episodes}\n"
)

ADMIN_MENU_ADD = "🎬 Yangi sarguzasht qo'shish"
ADMIN_MENU_ADD_EP = "➕ Mavjudga qism qo'shish"
ADMIN_MENU_LIST = "📋 Sarguzashtlar ro'yxati"
ADMIN_MENU_CHANNELS = "⛩️ Torii darvozalari"
ADMIN_MENU_BROADCAST = "📢 Xabar yuborish"
ADMIN_MENU_FEEDBACK = "✉️ Kelgan maktublar"
ADMIN_MENU_STATS = "📊 To'liq statistika"

ASK_NEW_TITLE = "📝 Yangi sarguzashtning nomi nima, Yaratuvchi-sama?"
NEW_ANIME_CREATED = (
    "🎉✨ <b>{title}</b> yaratildi! Kodi: <code>{code}</code>\n\n"
    "Endi qismlarni ketma-ket forward qiling, men hammasini o'zim tartiblayman! 🌸\n"
    "Tugatgach ✅ tugmasini bosing."
)
EPISODE_ADDED = "✅ {num}-qism qo'shildi! Yana forward qiling yoki ✅ Tugatish bosing."
FINISH_BTN = "✅ Tugatish"
ADDING_FINISHED = "🎊 Ajoyib! <b>{title}</b> uchun jami {count} ta qism saqlandi! 🍥"

ASK_ANIME_CODE_FOR_EP = "🔢 Qaysi animega qism qo'shmoqchisiz? Kodini yuboring:"
ANIME_FOUND_FOR_EP = "✅ Topildi: <b>{title}</b> (hozir {count} ta qism bor). Endi yangi qismlarni forward qiling!"

ASK_CHANNEL_ID = (
    "⛩️ Kanal/guruh username yoki ID sini yuboring.\n"
    "Masalan: <code>@mychannel</code> yoki <code>-1001234567890</code>\n\n"
    "⚠️ Bot o'sha kanalda <b>admin</b> bo'lishi shart!"
)
ASK_CHANNEL_TITLE = "📝 Endi bu kanal uchun ko'rsatiladigan nom kiriting (masalan: Asosiy kanal):"
ASK_CHANNEL_URL = "🔗 Endi shu kanalga taklif havolasini (link) yuboring:"
CHANNEL_ADDED = "✅ Torii darvozasi qo'shildi! 🌸"

ASK_BROADCAST_TEXT = "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:"
BROADCAST_STARTED = "🚀 Yuborish boshlandi... biroz kuting"
BROADCAST_DONE = "✅ Yuborildi! {success} ta odamga yetib bordi, {fail} ta xato."

ASK_FEEDBACK_NONE = "✉️ Hozircha yangi maktublar yo'q 🌸"

STATS_TEXT = (
    "📊✨ <b>To'liq hisobot, Yaratuvchi-sama!</b>\n\n"
    "👥 Jami foydalanuvchilar: {users}\n"
    "📈 Bugun qo'shilgan: +{today}\n"
    "🎴 Jami animelar: {anime} | Jami qismlar: {episodes}\n"
    "👍 {likes} | 👎 {dislikes}\n"
    "✉️ Jami maktublar: {feedback}\n"
    "⛩️ Majburiy obuna: {sub_status} ({channels} ta kanal)\n\n"
    "🔥 <b>Top-5 anime:</b>\n{top_list}"
)

NOT_ADMIN = "😅 Gomen, bu buyruq faqat Yaratuvchi-sama uchun..."
