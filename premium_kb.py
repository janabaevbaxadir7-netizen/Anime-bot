from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def premium_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 SOTIB OLISH", callback_data="premium_buy")],
            [InlineKeyboardButton(text="🎥 Qo'llanma - video ko'rish", url="https://t.me/Mr_Baxadir")],
            [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
        ]
    )


def premium_admin_decision_kb(request_id: int, tg_id: int) -> InlineKeyboardMarkup:
    """Admin panelga keladigan premium so'rov uchun tasdiqlash/rad etish tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"premapprove_{request_id}_{tg_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"premreject_{request_id}_{tg_id}"),
            ]
        ]
    )
