import asyncio
from aiogram import Bot
import crud


async def _check_one(bot: Bot, ch, user_id: int):
    """Bitta kanal bo'yicha obunani tekshiradi. Xatolik (masalan noto'g'ri
    saqlangan chat_id) bo'lsa ham, ehtiyot shart bilan 'obuna emas' deb hisoblaydi —
    lekin bu holatning oldini olish uchun kanal QO'SHILAYOTGANDA tekshirilishi kerak
    (admin.py dagi ch_add_id shu ishni qiladi)."""
    try:
        member = await bot.get_chat_member(chat_id=ch.chat_id, user_id=user_id)
        if member.status in ("left", "kicked"):
            return ch
    except Exception:
        return ch
    return None


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Barcha ro'yxatdagi kanallarga a'zoligini tekshiradi.
    Agar hech qanday kanal qo'shilmagan bo'lsa, tekshiruv o'tkazilmaydi (True qaytadi).
    MUHIM: kanallar PARALLEL tekshiriladi (ketma-ket emas) — bir necha majburiy
    obuna kanali bo'lganda /start tezligini sezilarli oshiradi."""
    channels = await crud.get_all_channels()
    if not channels:
        return True, []

    results = await asyncio.gather(*[_check_one(bot, ch, user_id) for ch in channels])
    not_subscribed = [ch for ch in results if ch is not None]

    return len(not_subscribed) == 0, not_subscribed
