import logging
import db

logger = logging.getLogger("yuki_bot")


async def smart_menu(bot, uid, text, reply_markup=None, photo=None):
    """Foydalanuvchiga yangi 'ekran' (menyu, panel yoki anime kartochkasi) ko'rsatadi
    va shu bilan birga OLDINGI shunday xabarni o'chirib tashlaydi — Meduza kabi botlar
    ishlatadigan 'toza chat' effekti. Video/qism xabarlari bunga kirmaydi (ular alohida
    qoladi, chunki foydalanuvchi ularni saqlab qolishi mumkin)."""
    user = await db.get_user(uid)
    if user and user.last_menu_msg_id:
        try:
            await bot.delete_message(uid, user.last_menu_msg_id)
        except Exception:
            pass  # xabar allaqachon o'chirilgan yoki juda eski bo'lishi mumkin

    try:
        if photo:
            sent = await bot.send_photo(uid, photo=photo, caption=text, reply_markup=reply_markup)
        else:
            sent = await bot.send_message(uid, text, reply_markup=reply_markup)
    except Exception as e:
        logger.warning("smart_menu yubora olmadi uid=%s: %s", uid, e)
        return None

    await db.set_last_menu_msg(uid, sent.message_id)
    return sent
