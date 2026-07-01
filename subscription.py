from aiogram import Bot
import db


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    is_on = await db.is_mandatory_sub_on()
    channels = await db.get_all_channels()

    if not is_on or not channels:
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
