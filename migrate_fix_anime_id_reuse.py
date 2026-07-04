"""
BIR MARTALIK MIGRATSIYA SKRIPTI — ANIME/EPISODE ID MUAMMOSINI TUZATADI.

NIMA UCHUN KERAK:
Eski kodda `animes` va `episodes` jadvallari SQLite'ning AUTOINCREMENT
kaliti bilan yaratilmagan edi. Shu sabab, anime o'chirilganda (ayniqsa
oxirgi qo'shilgan animelar o'chirilganda), SQLite o'sha o'chirilgan
animening ID'sini KEYINGI yangi animega QAYTA berib yuborar edi.

Bunga qo'shimcha, eski `delete_anime()` funksiyasi animeni o'chirganda
uning qismlarini (episodes) o'chirmas edi — ular bazada "etim" bo'lib
qolib ketardi. Natijada: ID qayta ishlatilganda, yangi anime avtomatik
ravishda o'sha eski "etim" qismlarni meros qilib olar edi — ya'ni eski
anime/qismlar yangi animega "yopishib qolar" edi.

BU SKRIPT NIMA QILADI:
  1. Hech qanday animega tegishli bo'lmagan "etim" qismlarni (episodes)
     topib, ularni bazadan tozalaydi (ular allaqachon noto'g'ri animega
     ulanib qolgan bo'lishi mumkin — xavfsiz tomoni shu qismlarni
     o'chirib, kerakli animelarga video fayllarni QAYTADAN yuklashdir).
  2. `animes` va `episodes` jadvallarini AUTOINCREMENT bilan qayta quradi
     — shundan keyin ID'lar HECH QACHON qayta ishlatilmaydi.

Qanday ishlatish (serveringizda, botni albatta TO'XTATIB turib):
    python migrate_fix_anime_id_reuse.py

Bu skriptni faqat BIR MARTA ishga tushirish kifoya. Agar jadval allaqachon
AUTOINCREMENT bilan bo'lsa, skript hech narsa buzmasdan shunchaki
"allaqachon tuzatilgan" deb chiqadi.
"""
import sqlite3
import re

from config import DB_PATH


def _sqlite_file_path(db_url: str) -> str:
    match = re.search(r"sqlite\+aiosqlite:///(.+)", db_url)
    if not match:
        raise RuntimeError(
            "Bu skript faqat SQLite baza uchun ishlaydi. DB_PATH sozlamangizni tekshiring."
        )
    return match.group(1)


def _table_has_autoincrement(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
    row = cur.fetchone()
    return bool(row and row[0] and "AUTOINCREMENT" in row[0].upper())


def main():
    path = _sqlite_file_path(DB_PATH)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    animes_ok = _table_has_autoincrement(cur, "animes")
    episodes_ok = _table_has_autoincrement(cur, "episodes")

    if animes_ok and episodes_ok:
        print("✅ 'animes' va 'episodes' jadvallari allaqachon AUTOINCREMENT bilan — hech narsa qilinmadi.")
        conn.close()
        return

    print("🔧 Migratsiya boshlandi...")

    # 1) Hech qanday animega tegishli bo'lmagan "etim" qismlarni tozalash
    cur.execute("SELECT COUNT(*) FROM episodes WHERE anime_id NOT IN (SELECT id FROM animes)")
    orphan_count = cur.fetchone()[0]
    if orphan_count:
        cur.execute("DELETE FROM episodes WHERE anime_id NOT IN (SELECT id FROM animes)")
        print(f"🧹 {orphan_count} ta 'etim' (egasiz qolgan) qism (episode) bazadan tozalandi.")
    else:
        print("🧹 Etim qism topilmadi.")

    # 2) animes jadvalini AUTOINCREMENT bilan qayta qurish
    if not animes_ok:
        cur.execute("ALTER TABLE animes RENAME TO animes_old")
        cur.execute("""
            CREATE TABLE animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                is_premium BOOLEAN,
                premium_free_at DATETIME,
                downloads INTEGER,
                cover_file_id VARCHAR(255),
                created_at DATETIME
            )
        """)
        cur.execute("""
            INSERT INTO animes (id, code, title, description, is_premium,
                                 premium_free_at, downloads, cover_file_id, created_at)
            SELECT id, code, title, description, is_premium,
                   premium_free_at, downloads, cover_file_id, created_at
            FROM animes_old
        """)
        cur.execute("DROP TABLE animes_old")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_animes_code ON animes(code)")
        print("✅ 'animes' jadvali AUTOINCREMENT bilan qayta qurildi.")

    # 3) episodes jadvalini AUTOINCREMENT + ON DELETE CASCADE bilan qayta qurish
    if not episodes_ok:
        cur.execute("ALTER TABLE episodes RENAME TO episodes_old")
        cur.execute("""
            CREATE TABLE episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_id INTEGER NOT NULL REFERENCES animes(id) ON DELETE CASCADE,
                part_number INTEGER,
                file_id VARCHAR(255)
            )
        """)
        cur.execute("""
            INSERT INTO episodes (id, anime_id, part_number, file_id)
            SELECT id, anime_id, part_number, file_id
            FROM episodes_old
        """)
        cur.execute("DROP TABLE episodes_old")
        print("✅ 'episodes' jadvali AUTOINCREMENT bilan qayta qurildi.")

    conn.commit()
    conn.close()
    print("🎉 Migratsiya muvaffaqiyatli yakunlandi! Endi botni oddiy tartibda ishga tushiring.")


if __name__ == "__main__":
    main()
