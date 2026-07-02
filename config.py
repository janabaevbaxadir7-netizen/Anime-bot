import os

# ==== ASOSIY SOZLAMALAR ====
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ_BU_YERGA")

# Admin/dasturchi ID'lari (statistika, premium boshqaruvi shu ID'larga ochiq)
ADMIN_IDS = [8094557015]  # Baxadir

# /dev komandasida ko'rsatiladigan username
DEV_USERNAME = "Mr_Baxadir"

# Kanal/guruh linklari (ixtiyoriy, agar reklama tugmalari kerak bo'lsa)
SUPPORT_CHAT = "https://t.me/Mr_Baxadir"

# Ma'lumotlar bazasi fayli
DB_PATH = "sqlite+aiosqlite:///animebot.db"
