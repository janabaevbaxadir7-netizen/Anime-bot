import os

# ==== ASOSIY SOZLAMALAR ====
# Railway'da "Variables" bo'limiga BOT_TOKEN nomi bilan tokenni qo'shsangiz,
# quyidagi qator avtomatik o'sha tokenni oladi.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8902500884:AAHb8NryHR-3M3xoviXeN_YdNA61tRkzOIk")

# Admin/dasturchi ID'lari (statistika, premium boshqaruvi shu ID'larga ochiq)
ADMIN_IDS = [8094557015]  # Baxadir

# /dev komandasida ko'rsatiladigan username
DEV_USERNAME = "Mr_Baxadir"

# Kanal/guruh linklari (ixtiyoriy, agar reklama tugmalari kerak bo'lsa)
SUPPORT_CHAT = "https://t.me/Mr_Baxadir"

# Ma'lumotlar bazasi fayli
DB_PATH = "sqlite+aiosqlite:///animebot.db"
