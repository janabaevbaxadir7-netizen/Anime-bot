from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config


def premium_kb() -> InlineKeyboardMarkup:
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
    rows = []
    if admin_id:
        # tg://user?id= — to'g'ridan-to'g'ri admin akkountiga ochiladi,
        # @username kerak emas, shuning uchun hech qachon buzilmaydi.
        rows.append([InlineKeyboardButton(text="💳 Admin bilan bog'lanish (sotib olish)", url=f"tg://user?id={admin_id}")])
    rows.append([InlineKeyboardButton(text="🎥 Qo'llanma - video ko'rish", url="https://t.me/Mr_Baxadir")])
    rows.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
