from aiogram.filters import BaseFilter

import config
import crud


class IsAdmin(BaseFilter):
    """Har qanday admin (bosh yoki dinamik) bo'lsa True."""
    async def __call__(self, event) -> bool:
        uid = event.from_user.id
        if uid in config.ADMIN_IDS:
            return True
        return (await crud.get_admin(uid)) is not None


class IsSuperAdmin(BaseFilter):
    """Faqat config.ADMIN_IDS dagi bosh adminlar uchun."""
    async def __call__(self, event) -> bool:
        return event.from_user.id in config.ADMIN_IDS


async def is_admin_async(uid: int) -> bool:
    if uid in config.ADMIN_IDS:
        return True
    return (await crud.get_admin(uid)) is not None


async def has_permission(uid: int, perm: str) -> bool:
    """Bosh adminlar har doim hamma narsaga ruxsatli. Dinamik adminlar
    faqat o'ziga berilgan 'permissions' ro'yxatidagi bo'limlarga kira oladi."""
    if uid in config.ADMIN_IDS:
        return True
    admin = await crud.get_admin(uid)
    if not admin:
        return False
    return perm in [p.strip() for p in admin.permissions.split(",") if p.strip()]
