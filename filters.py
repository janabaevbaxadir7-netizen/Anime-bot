from aiogram.filters import BaseFilter

import config
import db


class IsAdmin(BaseFilter):
    """Foydalanuvchi admin bo'lsa True qaytaradi — .env dagi bosh adminlar
    HAM bazada qo'shilgan (dinamik) adminlar hisobga olinadi."""
    async def __call__(self, event) -> bool:
        uid = event.from_user.id
        if uid in config.SUPER_ADMIN_IDS:
            return True
        return await db.is_db_admin(uid)


class IsSuperAdmin(BaseFilter):
    """Faqat .env dagi SUPER_ADMIN_IDS ro'yxatidagilar uchun True.
    Admin qo'shish/o'chirish kabi og'ir amallar shu filtr bilan himoyalanadi,
    shunda oddiy (dinamik) admin boshqa adminni o'chira olmaydi."""
    async def __call__(self, event) -> bool:
        return event.from_user.id in config.SUPER_ADMIN_IDS


async def is_admin_async(uid: int) -> bool:
    """Handler ichida to'g'ridan-to'g'ri chaqirish uchun yordamchi funksiya."""
    if uid in config.SUPER_ADMIN_IDS:
        return True
    return await db.is_db_admin(uid)
  
