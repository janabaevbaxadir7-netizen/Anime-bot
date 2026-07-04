import os
import sys

# ==== ASOSIY SOZLAMALAR ====
# Railway'da "Variables" bo'limiga BOT_TOKEN va ADMIN_IDS ni qo'shing.
# ESLATMA: bu yerda hech qanday standart (fallback) token YOZILMAYDI —
# eski tokeningiz allaqachon oshkor bo'lgan edi, shuning uchun kodda
# hardcoded token qoldirish xavfsizlik uchun mumkin emas.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Bosh adminlar (superadmin) — vergul bilan ajratilgan ID'lar, masalan: "8094557015,111111"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x]

DB_PATH = os.getenv("DB_PATH", "sqlite+aiosqlite:///animebot.db")


def validate():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS")
    if missing:
        print(f"❌ Railway 'Variables' bo'limida quyidagilar to'ldirilmagan: {', '.join(missing)}")
        sys.exit(1)
