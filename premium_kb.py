from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import crud


async def premium_kb() -> InlineKeyboardMarkup:
    admin_id = await crud.get_responsible_admin("premium")
    rows = [[InlineKeyboardButton(text="💎 Premium so'rash", callback_data="premium_request")]]
    if admin_id:
        # tg://user?id= — to'g'ridan-to'g'ri admin akkountiga ochiladi,
        # @username kerak emas, shuning uchun hech qachon buzilmaydi.
        rows.append([InlineKeyboardButton(text="💬 Admin bilan shaxsan bog'lanish", url=f"tg://user?id={admin_id}")])
    rows.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Admin tomoni: foydalanuvchi "Premium so'rash" bosganda unga yuboriladigan tezkor tanlov ──
def premium_grant_kb(target_uid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for days, label in [(7, "7 kun"), (30, "30 kun"), (90, "90 kun"), (365, "1 yil")]:
        kb.button(text=f"💎 {label}", callback_data=f"premgrant:{target_uid}:{days}")
    kb.button(text="✍️ Boshqa muddat", callback_data=f"premgrant_custom:{target_uid}")
    kb.button(text="❌ Rad etish", callback_data=f"premgrant_reject:{target_uid}")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()
