# ⛩️🌸 Sakura no Sekai — Anime bot (Yuki-chan)

To'liq tayyor Telegram bot: anime/qism qidirish, majburiy obuna, admin panel,
qismli (multi-episode) anime tizimi. Server: 0.5 GB RAM/disk uchun mos
(faqat matn+raqamlar saqlanadi, video Telegram serverida qoladi).

## 1. O'rnatish

```bash
# Python 3.10+ kerak
pip install -r requirements.txt
```

## 2. Sozlash

`config.py` faylini oching (yoki muhit o'zgaruvchilarini sozlang):

```bash
export BOT_TOKEN="123456:ABC-sizning-tokeningiz"
export ADMIN_IDS="123456789,987654321"   # bir nechta bo'lsa vergul bilan
```

Token olish: Telegramda **@BotFather** ga `/newbot` yuboring.
Sizning Telegram ID: **@userinfobot** ga `/start` yuboring.

## 3. Ishga tushirish

```bash
python bot.py
```

Konsolda `⛩️✨ Yuki-chan uyg'ondi!` yozuvi chiqsa — bot ishlayapti.

## 4. Qanday ishlatish

### Foydalanuvchi uchun
1. Botga `/start` yuboradi
2. Agar majburiy kanal bo'lsa, obuna bo'lib "✅ Tekshirish" bosadi
3. Murojaat turini tanlaydi (Senpai/Hime-chan)
4. "⛩️ Anime izlash" → kodni kiritadi → qismlar ro'yxati chiqadi → istalganini bosadi

### Admin uchun
1. `/admin` yuboradi (faqat `ADMIN_IDS` da bo'lganlar)
2. **"🎬 Yangi sarguzasht qo'shish"** — nom kiritadi, keyin videolarni ketma-ket
   **forward** qiladi (kanaldan), bot avtomatik 1, 2, 3... deb raqamlaydi,
   oxirida "✅ Tugatish" bosiladi
3. **"➕ Mavjudga qism qo'shish"** — keyinchalik (masalan 13-qism chiqqanda)
   shu orqali kodni kiritib, yangi videoni forward qilish kifoya
4. **"⛩️ Torii darvozalari"** — majburiy kanal qo'shish/o'chirish, va
   "Majburiy obuna: Yoqilgan/O'chirilgan" tugmasi orqali butunlay yoqib-o'chirish
5. **"📢 Xabar yuborish"** — barcha foydalanuvchilarga bitta xabar (broadcast)
6. **"✉️ Kelgan maktublar"** — userlar yuborgan taklif/shikoyatlar avtomatik
   sizga forward qilinadi, alohida ko'rish shart emas
7. **"📊 To'liq statistika"** — userlar soni, top animelar, like/dislike va h.k.

⚠️ **Muhim**: bot majburiy kanalda ishlashi uchun o'sha kanal/guruhda
**admin** qilib qo'yilgan bo'lishi shart (a'zolarni ko'rish huquqi bilan).

## 5. Bepul serverga joylashtirish (Oracle Cloud Always Free)

1. [Oracle Cloud](https://www.oracle.com/cloud/free/) da bepul akkaunt oching
2. "Always Free" VM yarating (Ubuntu, ARM yoki AMD — ikkalasi ham bepul)
3. SSH orqali ulaning, so'ng:

```bash
sudo apt update && sudo apt install python3-pip -y
git clone <repo-yoki-fayllarni-yuklang>
cd animebot
pip3 install -r requirements.txt
export BOT_TOKEN="..." ADMIN_IDS="..."
nohup python3 bot.py > bot.log 2>&1 &
```

Bot doimiy ishlashi uchun `systemd` xizmat sifatida sozlash tavsiya etiladi
(server qayta ishga tushganda avtomatik ishga tushishi uchun). Xohlasangiz
shu bo'yicha ham systemd fayl tayyorlab beraman.

## 6. Texnik tuzilma

```
animebot/
├── bot.py              # ishga tushirish nuqtasi
├── config.py            # token, admin ID
├── texts.py              # barcha xabar matnlari (shu yerdan tahrirlanadi)
├── states.py             # FSM holatlari
├── database/
│   ├── models.py         # SQLAlchemy modellari
│   └── db.py              # baza so'rovlari
├── keyboards/
│   ├── user_kb.py
│   └── admin_kb.py
├── handlers/
│   ├── user.py
│   └── admin.py
└── utils/
    └── subscription.py    # majburiy obuna tekshiruvi
```

Baza: SQLite (`sakura.db` fayli avtomatik yaratiladi) — qo'shimcha server
(Postgres/MySQL) shart emas, 0.5 GB chegara uchun yetarli va eng tezkor.
