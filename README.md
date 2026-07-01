# ⛩️🌸 Sakura no Sekai — Anime bot (Yuki-chan)

To'liq tayyor Telegram bot: anime/qism qidirish, majburiy obuna, admin panel,
qismli (multi-episode) anime tizimi, muqova+tavsif, dinamik adminlar,
anti-flood himoya va avtomatik xatolik loglash. Server: 0.5 GB RAM/disk
uchun mos (faqat matn+raqamlar saqlanadi, video Telegram serverida qoladi).

## 1. O'rnatish

```bash
# Python 3.10+ kerak
pip install -r requirements.txt
```

## 2. Sozlash (.env — MUHIM, xavfsizlik uchun)

`.env.example` faylidan nusxa oling va `.env` deb saqlang:

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:

```
BOT_TOKEN=123456:ABC-sizning-yangi-tokeningiz
SUPER_ADMIN_IDS=123456789,987654321
```

⚠️ **Token olish**: @BotFather ga `/newbot`. Agar avvalgi tokeningiz
biror joyda (screenshot, chat, GitHub) oshkor bo'lgan bo'lsa, albatta
@BotFather orqali `/revoke` qilib, YANGISINI oling.

Sizning Telegram ID: **@userinfobot** ga `/start` yuboring.

`.env` fayli **hech qachon** GitHub'ga yoki boshqa hech kimga yuborilmasin
— `.gitignore` da avtomatik chetlab o'tiladi.

## 3. Ishga tushirish

```bash
python bot.py
```

Konsol va `bot.log` faylida `⛩️✨ Yuki-chan uyg'ondi!` yozuvi chiqsa —
bot ishlayapti. Agar `.env` to'ldirilmagan bo'lsa, bot xato haqida yozib
to'xtaydi (buni oldindan aniqlash uchun махsус tekshiruv qo'yilgan).

## 4. Qanday ishlatish

### Foydalanuvchi uchun
1. Botga `/start` yuboradi
2. Agar majburiy kanal bo'lsa, obuna bo'lib "✅ Tekshirish" bosadi
3. Murojaat turini tanlaydi (Senpai/Hime-chan)
4. "🔍 Qidirish" → kodni kiritadi → qismlar ro'yxati chiqadi → istalganini bosadi

### Admin uchun
1. `/admin` yuboradi (`.env` dagi `SUPER_ADMIN_IDS` yoki botdan qo'shilgan admin)
2. **"🎬 Yangi anime"** — nom kiritadi, videolarni ketma-ket forward qiladi,
   oxirida "✅ Tugatish" bosiladi
3. **"➕ Qism qo'shish"** — mavjud animega yangi qism qo'shadi
4. Anime ro'yxatidan istalgan animeni ochib **tavsif** va **muqova rasm**
   qo'shish/o'zgartirish mumkin
5. **"⛩️ Kanallar"** — majburiy obuna kanallari va yoqish/o'chirish
6. **"📢 Xabar yuborish"** — barcha foydalanuvchilarga broadcast; botni
   bloklagan userlar endi avtomatik "faol emas" deb belgilanadi
7. **"✉️ Murojaatlar"**, **"📊 Statistika"**, **"💎 Premium so'rovlar"**
8. **"🛡 Adminlar"** — (faqat `.env` dagi bosh adminlar uchun) botdan turib
   yangi admin qo'shish yoki o'chirish — kodni qayta deploy qilish shart emas
9. **"👤 Foydalanuvchi rejimi"** — admin o'z botini oddiy foydalanuvchi
   sifatida sinab ko'rishi uchun; `/admin` bilan istalgan payt qaytadi

⚠️ **Muhim**: bot majburiy kanalda ishlashi uchun o'sha kanal/guruhda
**admin** qilib qo'yilgan bo'lishi shart (a'zolarni ko'rish huquqi bilan).

## 5. Ishonchlilik va xavfsizlik

- **Anti-flood**: bir foydalanuvchi juda tez-tez xabar yuborsa, ortiqcha
  so'rovlar `THROTTLE_RATE_LIMIT` (standart 0.7s) ichida e'tiborsiz qoldiriladi.
- **Xatoliklarni kuzatish**: har qanday handler xatoligi `bot.log` fayliga
  yoziladi va super-adminlarga Telegram orqali darhol xabar beriladi.
- **Sirlar**: token va admin ID lar endi kodda emas, `.env` da.

## 6. Bepul serverga joylashtirish (Oracle Cloud Always Free / Railway)

```bash
sudo apt update && sudo apt install python3-pip -y
git clone <repo-yoki-fayllarni-yuklang>
cd animebot
pip3 install -r requirements.txt
cp .env.example .env   # va to'ldiring
nohup python3 bot.py > /dev/null 2>&1 &
```

Bot doimiy ishlashi uchun `systemd` xizmat sifatida sozlash tavsiya etiladi.

## 7. Texnik tuzilma

```
animebot/
├── bot.py            # ishga tushirish nuqtasi, logging, middleware ulash
├── config.py         # .env dan sozlamalarni o'qiydi va tekshiradi
├── filters.py         # IsAdmin / IsSuperAdmin (dinamik admin tekshiruvi)
├── middlewares.py      # anti-flood + xatolik loglash
├── texts.py             # barcha xabar matnlari
├── states.py             # FSM holatlari
├── models.py              # SQLAlchemy modellari (Admin jadvali bilan)
├── db.py                   # baza so'rovlari
├── user_kb.py / admin_kb.py  # klaviaturalar
├── handlers_user.py / handlers_admin.py
├── subscription.py            # majburiy obuna tekshiruvi
├── .env.example                 # nusxa ko'chirib .env qiling
└── .gitignore
```

Baza: SQLite (`sakura.db` fayli avtomatik yaratiladi).
