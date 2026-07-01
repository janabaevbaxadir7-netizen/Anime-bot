import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Super-adminlar — .env dagi SUPER_ADMIN_IDS ichida, vergul bilan ajratilgan
# Bu ro'yxat kod ichida qattiq yozilgan, faqat .env orqali o'zgaradi.
# Boshqa (oddiy) adminlar botning o'zidan /add_admin buyrug'i orqali qo'shiladi
# va bazada saqlanadi (models.Admin), shuning uchun deploy qilmasdan boshqarish mumkin.
_super_ids = os.getenv("SUPER_ADMIN_IDS", "")
SUPER_ADMIN_IDS = [int(x) for x in _super_ids.replace(" ", "").split(",") if x]

DB_PATH = os.getenv("DB_PATH", "sakura.db")
BOT_NAME = os.getenv("BOT_NAME", "Yuki-chan")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Anti-flood: bitta foydalanuvchi shu vaqt oralig'ida (soniya) nechta xabar yubora oladi
THROTTLE_RATE_LIMIT = float(os.getenv("THROTTLE_RATE_LIMIT", "0.7"))


def validate():
    """Bot ishga tushishidan oldin majburiy sozlamalarni tekshiradi."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not SUPER_ADMIN_IDS:
        missing.append("SUPER_ADMIN_IDS")
    if missing:
        print(f"❌ .env faylida quyidagilar to'ldirilmagan: {', '.join(missing)}")
        print("   .env.example faylidan nusxa ko'chirib, .env deb saqlang va to'ldiring.")
        sys.exit(1)
      
