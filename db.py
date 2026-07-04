from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DB_PATH
from models import Base

engine = create_async_engine(DB_PATH, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# SQLite standart holatda FOREIGN KEY cheklovlarini (masalan, ON DELETE CASCADE)
# tekshirmaydi — buni har bir ulanishda alohida yoqish kerak.
# Shu bilan birga WAL (Write-Ahead Logging) rejimini yoqamiz: standart DELETE
# jurnal rejimida har bir yozish butun bazani vaqtincha qulflab qo'yadi, shu sabab
# bir vaqtda ko'p foydalanuvchi bo'lganda bot "sekinlashadi" yoki hatto
# "database is locked" xatosi berishi mumkin edi. WAL rejimida o'qish va yozish
# bir-biriga deyarli xalaqit bermaydi — bot sezilarli tezlashadi.
@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


async def init_db():
    """Bot ishga tushganda jadvallarni yaratadi (agar mavjud bo'lmasa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
