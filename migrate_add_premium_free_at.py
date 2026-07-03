"""
BIR MARTALIK MIGRATSIYA SKRIPTI.

Nima uchun kerak: models.py dagi Anime jadvaliga yangi "premium_free_at" ustuni
qo'shildi. init_db() faqat YO'Q jadvallarni yaratadi, lekin BOR jadvalga yangi
ustun qo'sha olmaydi. Shuning uchun eski bazangizda bu ustun yo'q va bot
xato berishi mumkin ("no such column: animes.premium_free_at").

Qanday ishlatish (Railway/Oracle serveringizda, botni to'xtatib turib):
    python migrate_add_premium_free_at.py

Bu skriptni faqat BIR MARTA ishga tushirish kerak. Ustun allaqachon bo'lsa,
xavfsiz — hech narsa buzmaydi, shunchaki "allaqachon bor" deb yozadi.
"""
import asyncio
import sqlite3
import re

from config import DB_PATH


def _sqlite_file_path(db_url: str) -> str:
    # "sqlite+aiosqlite:///animebot.db" -> "animebot.db"
    match = re.search(r"sqlite\+aiosqlite:///(.+)", db_url)
    if not match:
        raise RuntimeError(
            "Bu skript faqat SQLite baza uchun ishlaydi. DB_PATH sozlamangizni tekshiring."
        )
    return match.group(1)


def main():
    path = _sqlite_file_path(DB_PATH)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(animes)")
    columns = [row[1] for row in cur.fetchall()]

    if "premium_free_at" in columns:
        print("✅ 'premium_free_at' ustuni allaqachon mavjud, hech narsa qilinmadi.")
    else:
        cur.execute("ALTER TABLE animes ADD COLUMN premium_free_at DATETIME")
        conn.commit()
        print("✅ 'premium_free_at' ustuni muvaffaqiyatli qo'shildi!")

    conn.close()


if __name__ == "__main__":
    main()
