from aiogram import Bot
import crud


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Barcha ro'yxatdagi kanallarga a'zoligini tekshiradi.
    Agar hech qanday kanal qo'shilmagan bo'lsa, tekshiruv o'tkazilmaydi (True qaytadi)."""
    channels = await crud.get_all_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch.chat_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    return len(not_subscribed) == 0, not_subscribed
