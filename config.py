import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKENINGIZNI_BU_YERGA_YOZING")
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()
]
DB_PATH = os.getenv("DB_PATH", "sakura.db")
BOT_NAME = "Yuki-chan"
